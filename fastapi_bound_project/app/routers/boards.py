"""자유게시판 CRUD를 처리하는 라우터입니다."""

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Board, User
from app.schemas import (
    BoardCreate,
    BoardDetailResponse,
    BoardListResponse,
    BoardUpdate,
)
from app.security import get_current_user

router = APIRouter(prefix="/boards", tags=["자유게시판"])


def to_board_detail_response(board: Board) -> BoardDetailResponse:
    """Board ORM 객체를 상세 응답 스키마로 변환합니다(작성자 정보 포함)."""
    return BoardDetailResponse(
        id=board.id,
        title=board.title,
        content=board.content,
        view_count=board.view_count,
        writer_id=board.writer.id,
        writer_name=board.writer.name,
        created_at=board.created_at,
        updated_at=board.updated_at,
    )


def to_board_list_response(board: Board) -> BoardListResponse:
    """Board ORM 객체를 목록 응답 스키마로 변환합니다(본문 content 제외)."""
    return BoardListResponse(
        id=board.id,
        title=board.title,
        view_count=board.view_count,
        writer_name=board.writer.name,
        created_at=board.created_at,
    )


@router.post(
    "",
    response_model=BoardDetailResponse,
    status_code=status.HTTP_201_CREATED,
    summary="게시글 등록",
)
def create_board(
    board_data: BoardCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """새 게시글을 등록합니다. 로그인이 필요합니다."""
    new_board = Board(
        title=board_data.title,
        content=board_data.content,
        user_id=current_user.id,
    )
    db.add(new_board)
    db.commit()
    db.refresh(new_board)
    return to_board_detail_response(new_board)


@router.get("", response_model=list[BoardListResponse], summary="게시글 전체 조회")
def get_boards(db: Session = Depends(get_db)):
    """모든 게시글을 최신순으로 조회합니다(가벼운 목록 응답). 로그인이 필요 없습니다."""
    boards = db.query(Board).order_by(Board.id.desc()).all()
    return [to_board_list_response(board) for board in boards]


@router.get("/{board_id}", response_model=BoardDetailResponse, summary="게시글 상세 조회")
def get_board(board_id: int, db: Session = Depends(get_db)):
    """게시글 하나를 상세 조회하고 조회수를 1 증가시킵니다."""
    board = db.query(Board).filter(Board.id == board_id).first()
    if not board:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="게시글을 찾을 수 없습니다.",
        )

    board.view_count += 1
    db.commit()
    db.refresh(board)
    return to_board_detail_response(board)


@router.put("/{board_id}", response_model=BoardDetailResponse, summary="게시글 수정")
def update_board(
    board_id: int,
    board_data: BoardUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """게시글을 수정합니다. 작성자 본인만 수정할 수 있습니다."""
    board = db.query(Board).filter(Board.id == board_id).first()
    if not board:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="게시글을 찾을 수 없습니다.",
        )

    if board.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="본인이 작성한 게시글만 수정할 수 있습니다.",
        )

    board.title = board_data.title
    board.content = board_data.content
    db.commit()
    db.refresh(board)
    return to_board_detail_response(board)


@router.delete(
    "/{board_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="게시글 삭제",
)
def delete_board(
    board_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """게시글을 삭제합니다. 작성자 본인만 삭제할 수 있습니다."""
    board = db.query(Board).filter(Board.id == board_id).first()
    if not board:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="게시글을 찾을 수 없습니다.",
        )

    if board.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="본인이 작성한 게시글만 삭제할 수 있습니다.",
        )

    db.delete(board)
    db.commit()
    # 204 No Content 이므로 본문 없이 응답합니다.
    return Response(status_code=status.HTTP_204_NO_CONTENT)
