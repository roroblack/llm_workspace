# -*- coding: utf-8 -*-
"""Minimal-token smoke test for Gemini and OpenAI planner paths."""

import os

from planning_core import make_plan, validate_plan


PROVIDERS = ("gemini", "openai")
GOAL = "테스트"
MAX_TOKENS = int(os.getenv("LLM_SMOKE_MAX_TOKENS", "128"))


def main() -> None:
    for provider in PROVIDERS:
        plan = make_plan(provider, GOAL, max_tokens=MAX_TOKENS)
        ok, reason = validate_plan(plan)
        if not ok:
            raise RuntimeError(f"{provider} plan validation failed: {reason}")
        print(f"{provider}: ok ({len(plan.steps)} steps)")


if __name__ == "__main__":
    main()
