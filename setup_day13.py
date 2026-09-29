from __future__ import annotations

import os

from dotenv import load_dotenv
from langfuse import get_client


load_dotenv()

PROMPT_NAME = os.getenv("LANGFUSE_PROMPT_NAME", "day13-chat")

V1_PROMPT = """Feature={{feature}}
Docs={{docs}}
Question={{message}}"""

V2_PROMPT = """Feature={{feature}}
Docs={{docs}}
Question={{message}}

Answer concisely in 3-5 bullet points."""


def show_prompt(langfuse, label: str) -> None:
    """Fetch a prompt by label and print the resolved version."""
    prompt = langfuse.get_prompt(
        PROMPT_NAME,
        label=label,
        type="text",
    )

    print(
        f"  {label}: "
        f"version={prompt.version}"
    )


def main() -> None:
    langfuse = get_client()

    print(f"Prompt: {PROMPT_NAME}")
    print("=" * 50)

    # ---------------------------------------------------------
    # 1. Create version 1
    # ---------------------------------------------------------
    print("\n[1] Creating version 1...")

    v1 = langfuse.create_prompt(
        name=PROMPT_NAME,
        type="text",
        prompt=V1_PROMPT,
        labels=["baseline", "production"],
    )

    print(f"Created v1: version={v1.version}")

    # ---------------------------------------------------------
    # 2. Create version 2
    # ---------------------------------------------------------
    print("\n[2] Creating version 2...")

    v2 = langfuse.create_prompt(
        name=PROMPT_NAME,
        type="text",
        prompt=V2_PROMPT,
        labels=["candidate"],
    )

    print(f"Created v2: version={v2.version}")

    # ---------------------------------------------------------
    # 3. Verify baseline and candidate
    # ---------------------------------------------------------
    print("\n[3] Checking labels...")

    show_prompt(langfuse, "baseline")
    show_prompt(langfuse, "candidate")
    show_prompt(langfuse, "production")

    # ---------------------------------------------------------
    # 4. Promote production to v2
    # ---------------------------------------------------------
    print("\n[4] Moving production to v2...")

    langfuse.update_prompt(
        name=PROMPT_NAME,
        version=v2.version,
        new_labels=["candidate", "production"],
    )

    print("Production after promotion:")
    show_prompt(langfuse, "production")

    # ---------------------------------------------------------
    # 5. Roll production back to v1
    # ---------------------------------------------------------
    print("\n[5] Rolling production back to v1...")

    langfuse.update_prompt(
        name=PROMPT_NAME,
        version=v1.version,
        new_labels=["baseline", "production"],
    )

    print("Production after rollback:")
    show_prompt(langfuse, "production")

    # Make sure queued Langfuse events are sent.
    langfuse.flush()

    print("\nDone.")


if __name__ == "__main__":
    main()
