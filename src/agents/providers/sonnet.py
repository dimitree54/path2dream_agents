import sys
from agents.coding_agent import CLIAgent, LimitExceededError, NothingToContinueError
from agents.send_email import send_email
from agents.utils import get_file_tags_suffix, parse_common_args, build_prompt

# todo support re-auth

LIMITS_EXCEEDED_ERROR = "5-hour limit reached"


class ClaudeAgent(CLIAgent):
    def __init__(
        self,
        model: str = "sonnet",
        files_to_always_include: list[str] | None = None,
        working_dir: str = "./",
    ):
        super().__init__(files_to_always_include, working_dir)
        self.model = model
        self.resumable = False

    def _build_cmd(self, prompt: str, files_to_include: list[str]) -> list[str]:
        prompt_suffix = get_file_tags_suffix(
            self.files_to_always_include + (files_to_include or []), self.working_dir
        )
        full_prompt = prompt + prompt_suffix

        cmd = [
            "claude",
            "--model",
            self.model,
            "--dangerously-skip-permissions",
            "--print",
            full_prompt,
        ]
        return cmd

    def run(self, prompt: str, files_to_include: list[str] | None = None) -> str:
        self.resumable = False
        content = super().run(prompt, files_to_include)
        if LIMITS_EXCEEDED_ERROR in content:
            raise LimitExceededError
        self.resumable = True
        return content

    def _build_resume_cmd(self, prompt: str) -> list[str]:
        cmd = [
            "claude",
            "--model",
            self.model,
            "--dangerously-skip-permissions",
            "--continue",
            "--print",
            prompt,
        ]
        return cmd

    def resume(self, prompt: str | None) -> str:
        if not self.resumable:
            raise NothingToContinueError
        content = super().resume()
        if LIMITS_EXCEEDED_ERROR in content:
            raise LimitExceededError
        return content


def main():
    args = parse_common_args()
    prompt = build_prompt(args.instructions, args.message)
    agent = ClaudeAgent()
    try:
        result = agent.run(prompt, files_to_include=args.files)
    except LimitExceededError:
        send_email("claude limits exceeded")
        sys.stdout.write("claude is not available right now")
        sys.exit(1)
    sys.stdout.write(result)
    sys.exit(0)


if __name__ == "__main__":
    main()
