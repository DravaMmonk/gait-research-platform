from __future__ import annotations

from hound_forward.agent.runtime import AgentRuntime
from hound_forward.bootstrap import build_service
from hound_forward.settings import PlatformSettings


def main() -> None:
    settings = PlatformSettings()
    service = build_service(settings)
    runtime = AgentRuntime(service=service, settings=settings)
    runtime.run_forever()


if __name__ == "__main__":
    main()
