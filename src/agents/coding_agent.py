from abc import ABC, abstractmethod
import time

from agents.utils import run_cli


class AuthRequiredError(Exception):
    pass


class LimitExceededError(Exception):
    pass


class NothingToContinueError(Exception):
    pass


class CodingAgent(ABC):
    @abstractmethod
    def run(self, prompt: str, files_to_include: list[str] | None = None) -> str:
        raise NotImplementedError

    @abstractmethod
    def resume(self, prompt: str | None = None) -> str:
        raise NotImplementedError


class CLIAgent(CodingAgent):
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


class WaitingOnLimitAgent(CodingAgent):
    def __init__(self, base_agent: CodingAgent, wait_hours: int = 4):
        self.base_agent = base_agent,
        self.wait_seconds = wait_hours * 60 * 60
    
    def run(self, prompt: str, files_to_include: list[str] | None = None) -> str:
        try:
            return self.base_agent.run(prompt, files_to_include)
        except LimitExceededError:
            time.sleep(self.wait_seconds)
            return self.base_agent.run(prompt, files_to_include)
    
    def resume(self, prompt: str) -> str:
        try:
            return self.base_agent.resume(prompt)
        except LimitExceededError:
            time.sleep(self.wait_seconds)
            return self.base_agent.resume(prompt)
    
    def __str__(self) -> str:
        return f"WaitingOnLimitAgent({str(self.base_agent)})"


class FallbackOnLimitAgent(CodingAgent):
    def __init__(self, base_agent: CodingAgent, fallback_agent: CodingAgent) -> None:
        self.base_agent = base_agent
        self.fallback_agent = fallback_agent
    
    def run(self, prompt: str, files_to_include: list[str] | None = None) -> str:
        try:
            return self.base_agent.run(prompt, files_to_include)
        except LimitExceededError:
            return self.fallback_agent.run(prompt, files_to_include)
    
    def resume(self, prompt: str) -> str:
        try:
            return self.base_agent.resume(prompt)
        except LimitExceededError:
            return self.fallback_agent.resume(prompt)
    
    def __str__(self) -> str:
        return f"FallbackOnLimitAgent({str(self.base_agent)}, {str(self.fallback_agent)})"


class LoggingToFileAgent(CodingAgent):
    def __init__(self, base_agent: CodingAgent, file_path: str) -> None:
        self.base_agent = base_agent
        self.file_path = file_path
    
    # todo implement this draft
    def run(self, prompt: str, files_to_include: list[str] | None = None) -> str:
        run_id = None  # todo generate id
        with open(self.file_path) as f: # if exist - append, if not - create
            f.append(f"{timestamp}: {run_id} Running {str(self.base_agent)} agent with prompt:\n")
            f.append(prompt)
        result = self.base_agent.run(prompt, files_to_include)
        with open(self.file_path) as f:
            f.append(f"\n\n{timestamp}: {run_id} Run result:\n{result}")
        return result
