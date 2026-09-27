"""Pre-action policy checks for browser operations."""

from __future__ import annotations

from urllib.parse import urljoin, urlparse

from playwright.async_api import Page

from .models import ActionKind, BrowserAction, BrowserPolicy


class PolicyViolation(RuntimeError):
    pass


class PolicyGuard:
    def __init__(self, policy: BrowserPolicy):
        self.policy = policy

    def validate_url(self, url: str) -> None:
        parsed = urlparse(url)
        if parsed.scheme not in self.policy.allowed_schemes or parsed.hostname not in self.policy.allowed_hosts:
            raise PolicyViolation(f"disallowed_origin:{parsed.scheme}://{parsed.hostname or ''}")

    async def validate_action(self, page: Page, action: BrowserAction) -> None:
        if action.kind not in self.policy.allowed_actions:
            raise PolicyViolation(f"disallowed_action:{action.kind.value}")
        if action.kind not in {ActionKind.CLICK, ActionKind.FILL, ActionKind.SELECT, ActionKind.CHECK, ActionKind.SCROLL}:
            return
        locator = page.get_by_role(action.role, name=action.name) if action.role and action.name else page.locator(action.selector or "")
        if await locator.count() == 0:
            return
        metadata = await locator.first.evaluate(
            "element => ({tag: element.tagName.toLowerCase(), type: element.getAttribute('type'), href: element.href || null})"
        )
        if metadata.get("type") in self.policy.forbidden_button_types:
            raise PolicyViolation(f"forbidden_button_type:{metadata['type']}")
        href = metadata.get("href")
        if href:
            self.validate_url(urljoin(page.url, href))

    def validate_step(self, step: int) -> None:
        if step > self.policy.max_steps:
            raise PolicyViolation("step_limit")

    def validate_recovery(self, count: int) -> None:
        if count > self.policy.max_recoveries:
            raise PolicyViolation("recovery_limit")
