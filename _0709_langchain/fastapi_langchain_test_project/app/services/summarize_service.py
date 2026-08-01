from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI


class SummaryConfigurationError(RuntimeError):
    """Raised when the summary service is not configured."""


class SummaryServiceError(RuntimeError):
    """Raised when the summary service fails."""


MAX_CHARS_PER_CHUNK = 12000


def split_text(text: str, max_chars: int = MAX_CHARS_PER_CHUNK) -> list[str]:
    paragraphs = [paragraph.strip() for paragraph in text.split("\n\n") if paragraph.strip()]
    chunks: list[str] = []
    current = ""

    for paragraph in paragraphs:
        if len(paragraph) > max_chars:
            if current:
                chunks.append(current.strip())
                current = ""
            chunks.extend(
                paragraph[index : index + max_chars]
                for index in range(0, len(paragraph), max_chars)
            )
            continue

        next_text = f"{current}\n\n{paragraph}".strip() if current else paragraph
        if len(next_text) > max_chars:
            chunks.append(current.strip())
            current = paragraph
        else:
            current = next_text

    if current:
        chunks.append(current.strip())

    return chunks or [text[:max_chars]]


async def summarize_text(text: str, api_key: str, model: str, language: str) -> str:
    if not api_key:
        raise SummaryConfigurationError("OPENAI_API_KEY is not configured.")

    try:
        llm = ChatOpenAI(
            model=model,
            temperature=0.2,
            openai_api_key=api_key,
        )
        chunks = split_text(text)

        if len(chunks) == 1:
            return (await _summarize_chunks(llm, chunks, language))[0]

        partial_summaries = await _summarize_chunks(llm, chunks, language)
        return await _combine_summaries(llm, partial_summaries, language)
    except SummaryConfigurationError:
        raise
    except Exception as exc:
        raise SummaryServiceError("Failed to summarize the PDF content.") from exc


async def _summarize_chunks(
    llm: ChatOpenAI, chunks: list[str], language: str
) -> list[str]:
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You summarize PDF content clearly and faithfully. "
                "Keep important facts, dates, entities, and action items.",
            ),
            (
                "human",
                "Summarize the following text in {language}.\n\n{text}",
            ),
        ]
    )
    chain = prompt | llm | StrOutputParser()
    # abatch runs every chunk concurrently instead of one-by-one.
    summaries = await chain.abatch(
        [{"text": chunk, "language": language} for chunk in chunks]
    )
    return [summary.strip() for summary in summaries]


async def _combine_summaries(llm: ChatOpenAI, summaries: list[str], language: str) -> str:
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You combine partial summaries into one concise final summary.",
            ),
            (
                "human",
                "Combine these partial summaries into one final summary in {language}.\n\n{summaries}",
            ),
        ]
    )
    chain = prompt | llm | StrOutputParser()
    result = await chain.ainvoke(
        {
            "summaries": "\n\n".join(summaries),
            "language": language,
        }
    )
    return result.strip()
