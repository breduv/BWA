from collections.abc import Mapping

from langchain_core.language_models import LanguageModelInput
from langchain_core.messages import AIMessage, SystemMessage
from langchain_core.runnables import Runnable, RunnableConfig

from app.agents.state import ChatState
from app.models.chat import ReplyMode


async def call_model(
    state: ChatState,
    config: RunnableConfig,
    *,
    model: Runnable[LanguageModelInput, AIMessage],
    prompts: Mapping[ReplyMode, str],
) -> dict[str, list[AIMessage]]:
    response = await model.ainvoke(
        [
            SystemMessage(content=prompts[state["mode"]]),
            *state["messages"],
        ],
        config=config,
    )
    return {"messages": [response]}
