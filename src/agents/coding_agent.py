from abc import ABC, abstractmethod

from agents.utils import run_cli


class AuthRequiredError(Exception):
    pass


class LimitExceededError(Exception):
    pass


class NothingToContinueError(Exception):
    pass


class CodingAgent(ABC):
    def __init__(
        self,
        files_to_always_include: list[str] | None = None,
        working_dir: str = "./",
    ):
        self.files_to_always_include: list[str] = files_to_always_include or list()
        self.working_dir = working_dir

    @abstractmethod
    def _build_cmd(self, prompt: str, files_to_include: list[str]) -> list[str]:
        raise NotImplementedError()

    def run(self, prompt: str, files_to_include: list[str] | None = None) -> str:
        cmd = self._build_cmd(prompt, files_to_include)
        return run_cli(cmd, working_dir=self.working_dir)

    @abstractmethod
    def _build_resume_cmd(self, prompt: str) -> list[str]:
        raise NotImplementedError()

    def resume(self, prompt: str | None = None) -> str:
        cmd = self._build_resume_cmd(prompt or "continue")
        return run_cli(cmd)
