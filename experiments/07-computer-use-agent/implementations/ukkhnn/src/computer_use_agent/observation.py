"""DOM/accessibility observation and optional screenshot capture."""

from __future__ import annotations

import hashlib

from playwright.async_api import Page

from .models import Observation


OBSERVATION_SCRIPT = """
() => {
  const text = selector => document.querySelector(selector)?.textContent?.trim() ?? null;
  const value = selector => document.querySelector(selector)?.value ?? null;
  const visible = element => {
    if (!element) return false;
    const rect = element.getBoundingClientRect();
    const style = getComputedStyle(element);
    return style.visibility !== 'hidden' && style.display !== 'none' && rect.width > 0 && rect.height > 0;
  };
  const selectorFor = element => {
    if (element.id) return `#${element.id}`;
    if (element.dataset.category) return `[data-category="${element.dataset.category}"]`;
    return element.tagName.toLowerCase();
  };
  const interactive = [...document.querySelectorAll('button,input,select,a,[role=tab]')]
    .filter(visible)
    .map(element => ({
      selector: selectorFor(element),
      role: element.getAttribute('role') || (element.tagName === 'A' ? 'link' : element.tagName === 'BUTTON' ? 'button' : null),
      name: element.getAttribute('aria-label') || element.textContent?.trim() || element.labels?.[0]?.textContent?.trim() || '',
      type: element.getAttribute('type'),
      href: element.href || null,
      value: element.value ?? null,
      checked: element.checked ?? null
    }));
  const scrollTarget = document.querySelector('#scroll-target');
  const rect = scrollTarget?.getBoundingClientRect();
  return {
    states: {
      search_input: value('#search-input'), search_status: text('#search-status'),
      filter_status: text('#filter-status'), profile_name: value('#profile-name'),
      profile_email: value('#profile-email'), form_error: text('#form-error'),
      profile_preview: text('#profile-preview'), tab_status: text('#tab-status'),
      scroll_status: text('#scroll-status'), scroll_target_in_view: !!rect && rect.top >= 0 && rect.bottom <= innerHeight,
      dynamic_status: text('#dynamic-status'), dynamic_exists: !!document.querySelector('#dynamic-button'),
      save_status: text('#save-status'), save_button_id: document.querySelector('#save-slot button')?.id ?? null,
      sort_value: value('#sort-select'), sort_status: text('#sort-status'),
      notifications: document.querySelector('#notifications')?.checked ?? false,
      notification_status: text('#notification-status'), policy_status: text('#policy-status'),
      external_status: text('#external-status')
    },
    elements: interactive
  };
}
"""


async def observe(page: Page, *, capture_screenshot: bool = False) -> Observation:
    payload = await page.evaluate(OBSERVATION_SCRIPT)
    screenshot_sha256 = None
    if capture_screenshot:
        screenshot = await page.screenshot(full_page=False)
        screenshot_sha256 = hashlib.sha256(screenshot).hexdigest()
    return Observation(
        url=page.url,
        title=await page.title(),
        states=payload["states"],
        elements=payload["elements"],
        screenshot_sha256=screenshot_sha256,
    )
