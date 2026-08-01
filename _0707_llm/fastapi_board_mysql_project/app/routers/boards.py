# app/routers/boards.py
# 자유게시글 CRUD API를 정의하는 라우터 파일입니다.

from fastapi import APIRouter, Depends, HTTPException, status  # 라우터, 의존성 주입, HTTP 오류를 사용합니다.
from sqlalchemy.orm import Session  # DB 세션 타입 힌트에 사용합니다.
from app.database import get_db  # DB 세션 의존성 함수입니다.
from app.models import Board, User  # 게시글과 회원 ORM 모델입니다.
from app.schemas import BoardCreate, BoardDetailResponse, BoardListResponse, BoardUpdate  # 게시글 요청/응답 스키마입니다.
from app.security import get_current_user  # 로그인 사용자 확인 의존성 함수입니다.

router = APIRouter(prefix="/boards", tags=["자유게시판"] )  # /boards로 시작하는 게시판 API 그룹을 만듭니다.


def to_board_detail_response(board: Board) -> BoardDetailResponse:
    # Board ORM 객체를 상세 응답 스키마로 변환하는 보조 함수입니다.
    return BoardDetailResponse(  # Pydantic 응답 객체를 생성합니다.
        id=board.id,  # 게시글 번호입니다.
        title=board.title,  # 게시글 제목입니다.
        content=board.content,  # 게시글 내용입니다.
        view_count=board.view_count,  # 게시글 조회수입니다.
        writer_id=board.writer.id,  # 작성자 번호입니다.
        writer_name=board.writer.name,  # 작성자 이름입니다.
        created_at=board.created_at,  # 작성 시각입니다.
        updated_at=board.updated_at,  # 수정 시각입니다.
    )


def to_board_list_response(board: Board) -> BoardListResponse:
    # Board ORM 객체를 목록 응답 스키마로 변환하는 보조 함수입니다.
    return BoardListResponse(  # Pydantic 목록 응답 객체를 생성합니다.
        id=board.id,  # 게시글 번호입니다.
        title=board.title,  # 게시글 제목입니다.
        view_count=board.view_count,  # 게시글 조회수입니다.
        writer_name=board.writer.name,  # 작성자 이름입니다.
        created_at=board.created_at,  # 작성 시각입니다.
    )


@router.post("", response_model=BoardDetailResponse, status_code=status.HTTP_201_CREATED)
def create_board(board_data: BoardCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # 로그인한 사용자만 게시글을 등록할 수 있는 API입니다.
    new_board = Board(  # DB에 저장할 새 게시글 ORM 객체를 생성합니다.
        title=board_data.title,  # 요청 제목을 저장합니다.
        content=board_data.content,  # 요청 내용을 저장합니다.
        user_id=current_user.id,  # 현재 로그인 사용자를 작성자로 저장합니다.
    )
    db.add(new_board)  # 새 게시글 객체를 DB 세션에 추가합니다.
    db.commit()  # INSERT 쿼리를 실제 DB에 반영합니다.
    db.refresh(new_board)  # DB에서 생성된 id와 시각 정보를 객체에 반영합니다.
    return to_board_detail_response(new_board)  # 생성된 게시글 상세 정보를 반환합니다.


@router.get("", response_model=list[BoardListResponse])
def get_boards(db: Session = Depends(get_db)):
    # 게시글 전체 목록을 조회하는 API입니다.
    boards = db.query(Board).order_by(Board.id.desc()).all()  # 게시글을 최신순으로 전체 조회합니다.
    return [to_board_list_response(board) for board in boards]  # 각 게시글을 목록 응답 구조로 변환해 반환합니다.


@router.get("/{board_id}", response_model=BoardDetailResponse)
def get_board(board_id: int, db: Session = Depends(get_db)):
    # 게시글 상세 조회 API입니다.
    # 이 API는 조회할 때마다 조회수를 1 증가시킵니다.
    board = db.query(Board).filter(Board.id == board_id).first()  # 게시글 번호로 게시글을 조회합니다.
    if not board:  # 게시글이 없으면 404 오류를 반환합니다.
        raise HTTPException(status_code=404, detail="게시글을 찾을 수 없습니다.")  # 존재하지 않는 게시글 오류입니다.

    board.view_count += 1  # 상세 조회 성공 시 조회수를 1 증가시킵니다.
    db.commit()  # UPDATE 쿼리를 실제 DB에 반영합니다.
    db.refresh(board)  # 증가된 조회수 값을 객체에 다시 반영합니다.
    return to_board_detail_response(board)  # 상세 응답을 반환합니다.


@router.put("/{board_id}", response_model=BoardDetailResponse)
def update_board(board_id: int, board_data: BoardUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # 로그인한 작성자만 게시글을 수정할 수 있는 API입니다.
    board = db.query(Board).filter(Board.id == board_id).first()  # 수정 대상 게시글을 조회합니다.
    if not board:  # 게시글이 없으면 404 오류를 반환합니다.
        raise HTTPException(status_code=404, detail="게시글을 찾을 수 없습니다.")  # 존재하지 않는 게시글 오류입니다.

    if board.user_id != current_user.id:  # 현재 로그인 사용자가 작성자인지 확인합니다.
        raise HTTPException(status_code=403, detail="본인이 작성한 게시글만 수정할 수 있습니다.")  # 권한 없음 오류입니다.

    board.title = board_data.title  # 제목을 새 값으로 변경합니다.
    board.content = board_data.content  # 내용을 새 값으로 변경합니다.
    db.commit()  # UPDATE 쿼리를 실제 DB에 반영합니다.
    db.refresh(board)  # 수정된 값을 객체에 다시 반영합니다.
    return to_board_detail_response(board)  # 수정된 게시글 상세 정보를 반환합니다.


@router.delete("/{board_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_board(board_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # 로그인한 작성자만 게시글을 삭제할 수 있는 API입니다.
    board = db.query(Board).filter(Board.id == board_id).first()  # 삭제 대상 게시글을 조회합니다.
    if not board:  # 게시글이 없으면 404 오류를 반환합니다.
        raise HTTPException(status_code=404, detail="게시글을 찾을 수 없습니다.")  # 존재하지 않는 게시글 오류입니다.

    if board.user_id != current_user.id:  # 현재 로그인 사용자가 작성자인지 확인합니다.
        raise HTTPException(status_code=403, detail="본인이 작성한 게시글만 삭제할 수 있습니다.")  # 권한 없음 오류입니다.

    db.delete(board)  # 게시글 삭제 SQL을 준비합니다.
    db.commit()  # DELETE 쿼리를 실제 DB에 반영합니다.
    return None  # 204 응답은 본문을 반환하지 않습니다.
