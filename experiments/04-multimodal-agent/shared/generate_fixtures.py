#!/usr/bin/env python3
"""Generate the shared, deterministic and non-personal multimodal fixtures."""

from __future__ import annotations

import hashlib
import json
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parent
FIXTURES = ROOT / "fixtures"
LABELS = ROOT / "labels"
CONTEXT = ROOT / "context"
EVALS = ROOT / "evals"
WIDTH, HEIGHT = 1280, 720

COLORS = {
    "navy": "#172033",
    "sidebar": "#202B42",
    "bg": "#F4F6FA",
    "card": "#FFFFFF",
    "text": "#172033",
    "muted": "#667085",
    "line": "#D8DEE9",
    "primary": "#356AE6",
    "success": "#17875D",
    "warning": "#C56A12",
    "danger": "#C8394A",
    "soft_blue": "#EAF0FF",
    "soft_red": "#FDECEF",
    "soft_green": "#E7F7EF",
}


@dataclass(frozen=True)
class FixtureSpec:
    fixture_id: str
    title: str
    scenario: str
    error_types: tuple[str, ...]
    severity: str
    evidence: tuple[dict[str, str], ...]
    uncertainty: str
    user_description: str
    dom_summary: str
    accessibility_snapshot: str
    visible_text: tuple[str, ...]


SPECS: tuple[FixtureSpec, ...] = (
    FixtureSpec("ui-error-001", "Checkout", "layout_overlap", ("layout_break",), "high", ({"region": "order-summary", "claim": "The Pay now button overlaps the order total."},), "The overlap is visually clear; its CSS cause is unknown.", "The checkout action covers part of the total.", "main > section.order-summary > total + button.primary", "heading Checkout; text Total 84 credits; button Pay now", ("Checkout", "Order summary", "Total 84 credits", "Pay now")),
    FixtureSpec("ui-error-002", "Analytics", "horizontal_overflow", ("layout_break",), "medium", ({"region": "main-content-right-edge", "claim": "The chart and its label continue beyond the visible viewport."},), "The hidden chart extent cannot be measured from the screenshot.", "The analytics chart is cut off on the right.", "main > section.chart[style='width:1460px']", "heading Analytics; chart Weekly sessions; label Saturday clipped", ("Analytics", "Weekly sessions", "Saturday")),
    FixtureSpec("ui-error-003", "Team board", "misaligned_cards", ("layout_break",), "low", ({"region": "task-grid", "claim": "The middle task card is vertically displaced from adjacent cards."},), "The intended grid alignment is inferred from neighboring cards.", "One project card does not line up with the others.", "main > section.task-grid > article:nth-child(2).offset", "heading Team board; three task cards", ("Team board", "Research", "Prototype", "Review")),
    FixtureSpec("ui-error-004", "Reports", "collapsed_content", ("layout_break",), "high", ({"region": "report-table", "claim": "Table columns are compressed until labels collide."},), "The responsive breakpoint that caused the collision is unknown.", "The report columns are stacked on top of one another.", "main > table.report.compact-broken", "table headers Period, Status, Amount overlap", ("Reports", "Period", "Status", "Amount")),
    FixtureSpec("ui-error-005", "Workspace setup", "clipped_button", ("element_clipping",), "high", ({"region": "setup-card-bottom", "claim": "The primary Continue button is clipped by the card boundary."},), "The portion below the card is not visible.", "I can only see the top half of Continue.", "main > form.setup > button.primary[aria-label='Continue']", "button Continue, partially visible", ("Workspace setup", "Choose preferences", "Continue")),
    FixtureSpec("ui-error-006", "Import data", "truncated_error", ("element_clipping", "error_message"), "medium", ({"region": "import-alert", "claim": "The error message ends mid-sentence inside a fixed-height alert."},), "The missing remainder of the message cannot be recovered visually.", "The import error text is truncated.", "main > div[role='alert'].fixed-height > p", "alert Import failed: unsupported col...", ("Import data", "Import failed: unsupported col...", "Try again")),
    FixtureSpec("ui-error-007", "Delete project", "clipped_modal", ("element_clipping",), "high", ({"region": "dialog-right-edge", "claim": "The dialog extends past the viewport and hides part of Delete."},), "Only the visible portion of the destructive action can be assessed.", "The confirmation dialog runs off screen.", "body > dialog.delete[open][style='left:1040px']", "dialog Delete project; destructive button partially hidden", ("Delete project", "This cannot be undone", "Cancel", "Delete")),
    FixtureSpec("ui-error-008", "Navigation", "missing_nav_label", ("element_clipping", "accessibility_issue"), "medium", ({"region": "sidebar-third-item", "claim": "The third navigation label is clipped to a single letter."},), "The complete intended label is available only from context.", "A sidebar label is unreadable.", "nav > a[aria-label='Reports'] > span.clipped", "navigation item Reports announced; visible text R", ("Navigation", "Home", "Projects", "R")),
    FixtureSpec("ui-error-009", "Notifications", "contradictory_toggle", ("invalid_state",), "medium", ({"region": "email-notifications-row", "claim": "The toggle appears on while the adjacent status says Disabled."},), "The authoritative state cannot be chosen from the screenshot alone.", "Email notifications look enabled and disabled at once.", "button[role='switch'][aria-checked='true'] + span.status-disabled", "switch Email notifications on; text Disabled", ("Notifications", "Email notifications", "Disabled")),
    FixtureSpec("ui-error-010", "File upload", "impossible_progress", ("invalid_state",), "high", ({"region": "upload-progress", "claim": "Upload progress is displayed as 128 percent."},), "Whether the value is a calculation or rendering error is unknown.", "The upload progress is over 100 percent.", "progress[value='128'][max='100']", "progress Upload 128 percent", ("File upload", "Uploading", "128%")),
    FixtureSpec("ui-error-011", "Plan selection", "multiple_single_choice", ("invalid_state",), "medium", ({"region": "plan-options", "claim": "Two radio-style plan options are selected simultaneously."},), "The screenshot does not reveal which plan should remain selected.", "Both Basic and Plus are selected.", "fieldset > input[type='radio']:checked x2", "radio Basic checked; radio Plus checked", ("Plan selection", "Basic", "Plus", "Continue")),
    FixtureSpec("ui-error-012", "Profile setup", "disabled_required_action", ("invalid_state",), "high", ({"region": "profile-form", "claim": "All required fields appear complete but Save remains disabled."},), "An unseen validation rule may exist, so the cause is uncertain.", "The completed form still cannot be saved.", "form[data-valid='true'] > button[disabled]", "three required fields complete; button Save disabled", ("Profile setup", "Display name", "Role", "Workspace", "Save")),
    FixtureSpec("ui-error-013", "Dashboard", "server_error", ("error_message",), "high", ({"region": "dashboard-alert", "claim": "A prominent alert reports that dashboard data could not load."},), "The upstream service and recovery time are not shown.", "The dashboard says its data failed to load.", "main > div[role='alert'][data-code='SERVER_ERROR']", "alert Could not load dashboard data", ("Dashboard", "Could not load dashboard data", "Retry")),
    FixtureSpec("ui-error-014", "Payment", "payment_failure", ("error_message",), "critical", ({"region": "payment-result", "claim": "The payment is marked Failed and no completion receipt is shown."},), "The reason for rejection is not exposed.", "The payment failed at confirmation.", "main > section.payment-result[data-state='failed']", "heading Payment failed; button Choose another method", ("Payment", "Payment failed", "No charge was made", "Choose another method")),
    FixtureSpec("ui-error-015", "Live metrics", "timeout_banner", ("error_message",), "medium", ({"region": "top-banner", "claim": "A timeout banner states that live metrics are stale."},), "The age of the last successful data point is approximate.", "The live metrics timed out.", "main > div[role='status'][data-state='timeout']", "status Live update timed out; chart Last update 12 min ago", ("Live metrics", "Live update timed out", "Last update 12 min ago")),
    FixtureSpec("ui-error-016", "Create workspace", "form_validation", ("error_message", "invalid_state"), "medium", ({"region": "workspace-name-field", "claim": "The form shows a required-field error while the field contains a visible value."},), "Whitespace or hidden validation rules could explain the error.", "The filled workspace name is still marked required.", "input[name='workspace'][value='Demo Lab'][aria-invalid='true']", "textbox Workspace name Demo Lab invalid; error Required field", ("Create workspace", "Workspace name", "Demo Lab", "Required field")),
    FixtureSpec("ui-error-017", "Account overview", "low_contrast", ("accessibility_issue",), "high", ({"region": "account-summary", "claim": "Key summary text uses very light gray on a white card."},), "Exact contrast ratio requires sampling colors; only an evident risk is asserted.", "The balance summary is almost invisible.", "section.summary > p.muted[style='color:#D5D8DE']", "text Current usage 64 credits with low visual contrast", ("Account overview", "Current usage", "64 credits")),
    FixtureSpec("ui-error-018", "Keyboard settings", "missing_focus", ("accessibility_issue",), "medium", ({"region": "shortcut-controls", "claim": "The focused Save shortcut button has no visible focus indicator."},), "Keyboard focus is supplied by the accessibility snapshot, not inferable from pixels alone.", "Keyboard focus is on Save, but I cannot see it.", "button#save-shortcut:focus-visible[style='outline:none']", "button Save shortcut focused; no visible focus indicator", ("Keyboard settings", "Save shortcut", "Reset")),
    FixtureSpec("ui-error-019", "System status", "color_only_status", ("accessibility_issue",), "medium", ({"region": "service-status-list", "claim": "Service health is communicated only by red and green dots."},), "The color meanings are inferred from conventional status colors.", "Status uses dots without text labels.", "ul.services > li > span.status-dot[aria-label='']", "service rows with unlabeled colored status indicators", ("System status", "API", "Storage", "Webhooks")),
    FixtureSpec("ui-error-020", "Mobile actions", "small_touch_target", ("accessibility_issue",), "low", ({"region": "card-actions", "claim": "Icon-only action controls are visibly much smaller than nearby buttons."},), "The exact CSS pixel size is intentionally not asserted.", "The card action icons are too small to target reliably.", "article > button.icon-only.small", "three icon buttons with small touch targets", ("Mobile actions", "Recent items", "Open", "Share")),
    FixtureSpec("ui-normal-021", "Checkout", "normal_checkout", (), "none", ({"region": "checkout", "claim": "The order summary and primary action are fully visible and separated."},), "Back-end behavior cannot be verified from a static screenshot.", "Checkout looks ready to submit.", "main > section.order-summary[data-state='ready']", "heading Checkout; total and Pay now button visible", ("Checkout", "Order summary", "Total 84 credits", "Pay now")),
    FixtureSpec("ui-normal-022", "Analytics", "normal_dashboard", (), "none", ({"region": "analytics", "claim": "Cards and chart fit within the viewport without collision."},), "Only the captured viewport is evaluated.", "The analytics page looks normal.", "main > section.metrics + section.chart", "heading Analytics; three metric cards; complete chart", ("Analytics", "Weekly sessions", "Conversion", "Retention")),
    FixtureSpec("ui-normal-023", "Notifications", "normal_settings", (), "none", ({"region": "notification-settings", "claim": "Each switch and status label communicates a consistent state."},), "Delivery outside the UI cannot be verified.", "Notification settings look consistent.", "main > form.notifications[data-valid='true']", "switch Email notifications on; text Enabled", ("Notifications", "Email notifications", "Enabled", "Save changes")),
    FixtureSpec("ui-normal-024", "Archive workspace", "normal_modal", (), "none", ({"region": "archive-dialog", "claim": "The complete dialog and both actions are visible inside the viewport."},), "The result of selecting an action is not tested.", "The archive confirmation dialog is fully visible.", "body > dialog.archive[open]", "dialog Archive workspace; buttons Cancel and Archive", ("Archive workspace", "You can restore it later", "Cancel", "Archive")),
)


TAXONOMY: dict[str, Any] = {
    "version": "1.0.0",
    "error_types": {
        "layout_break": "Elements overlap, collide, overflow, or lose their intended layout.",
        "element_clipping": "Meaningful text or controls are cut off by a container or viewport.",
        "invalid_state": "The screen presents contradictory, impossible, or unusable state.",
        "error_message": "The screen visibly reports an application or validation failure.",
        "accessibility_issue": "Visible or contextual evidence indicates an accessibility barrier.",
    },
    "severity": {
        "none": "No observed defect.",
        "low": "Minor friction with a viable workaround.",
        "medium": "Material friction or ambiguity in a non-critical path.",
        "high": "A primary task is blocked or seriously impaired.",
        "critical": "A destructive, financial, security, or system-wide outcome is at risk.",
    },
    "evidence_policy": "Name a visible region and claim only what is directly visible or explicitly supplied by the compact context. Never invent pixel-level coordinates.",
}


def _font(size: int, *, bold: bool = False) -> ImageFont.FreeTypeFont:
    candidates = (
        Path("/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
    )
    for candidate in candidates:
        if candidate.is_file():
            return ImageFont.truetype(str(candidate), size)
    raise RuntimeError("Arial 또는 DejaVu Sans font를 찾을 수 없습니다.")


def _text(draw: ImageDraw.ImageDraw, xy: tuple[int, int], value: str, size: int = 22, *, fill: str | None = None, bold: bool = False) -> None:
    draw.text(xy, value, font=_font(size, bold=bold), fill=fill or COLORS["text"])


def _rounded(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], *, fill: str, outline: str | None = None, radius: int = 16, width: int = 1) -> None:
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def _base(title: str) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    image = Image.new("RGB", (WIDTH, HEIGHT), COLORS["bg"])
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, 238, HEIGHT), fill=COLORS["sidebar"])
    _text(draw, (34, 34), "Northstar", 28, fill="#FFFFFF", bold=True)
    for index, label in enumerate(("Overview", "Projects", "Reports", "Settings")):
        y = 116 + index * 58
        if (index + len(title)) % 4 == 0:
            _rounded(draw, (20, y - 10, 218, y + 36), fill="#2E3B59", radius=10)
        _text(draw, (48, y), label, 18, fill="#D9E0EF")
    _text(draw, (278, 42), title, 34, bold=True)
    _text(draw, (280, 91), "Synthetic test workspace", 16, fill=COLORS["muted"])
    return image, draw


def _button(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], label: str, *, fill: str | None = None, text_fill: str = "#FFFFFF", disabled: bool = False) -> None:
    color = "#B8C0CC" if disabled else (fill or COLORS["primary"])
    _rounded(draw, box, fill=color, radius=10)
    bbox = draw.textbbox((0, 0), label, font=_font(18, bold=True))
    x = box[0] + (box[2] - box[0] - (bbox[2] - bbox[0])) // 2
    y = box[1] + (box[3] - box[1] - (bbox[3] - bbox[1])) // 2 - 2
    _text(draw, (x, y), label, 18, fill=text_fill, bold=True)


def _card(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], heading: str, body: str = "") -> None:
    _rounded(draw, box, fill=COLORS["card"], outline=COLORS["line"])
    _text(draw, (box[0] + 24, box[1] + 22), heading, 20, bold=True)
    if body:
        _text(draw, (box[0] + 24, box[1] + 62), body, 16, fill=COLORS["muted"])


def _render(spec: FixtureSpec) -> Image.Image:
    image, draw = _base(spec.title)
    s = spec.scenario

    if s in {"layout_overlap", "normal_checkout"}:
        _card(draw, (280, 145, 1160, 600), "Order summary", "Review the items before confirming.")
        _text(draw, (330, 292), "Workspace credits", 20)
        _text(draw, (885, 292), "84 credits", 20, bold=True)
        draw.line((330, 348, 1110, 348), fill=COLORS["line"], width=2)
        _text(draw, (330, 395), "Total", 26, bold=True)
        _text(draw, (870, 395), "84 credits", 26, bold=True)
        _button(draw, (830, 470 if s == "normal_checkout" else 382, 1110, 530 if s == "normal_checkout" else 448), "Pay now")
    elif s in {"horizontal_overflow", "normal_dashboard"}:
        for i, (name, value) in enumerate((("Sessions", "2,480"), ("Conversion", "6.4%"), ("Retention", "82%"))):
            x = 280 + i * 288
            _card(draw, (x, 140, x + 260, 258), name, value)
        _card(draw, (280, 292, 1210, 650), "Weekly sessions")
        width = 1040 if s == "horizontal_overflow" else 840
        points = [(330 + i * (width // 6), 570 - ((i * 53) % 180)) for i in range(7)]
        draw.line(points, fill=COLORS["primary"], width=6, joint="curve")
        for x, y in points:
            draw.ellipse((x - 6, y - 6, x + 6, y + 6), fill=COLORS["primary"])
        for i, label in enumerate(("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")):
            _text(draw, (320 + i * (width // 6), 610), label, 14, fill=COLORS["muted"])
    elif s == "misaligned_cards":
        for i, name in enumerate(("Research", "Prototype", "Review")):
            x = 280 + i * 295
            y = 165 + (90 if i == 1 else 0)
            _card(draw, (x, y, x + 260, y + 235), name, f"Task group {i + 1}")
            _button(draw, (x + 24, y + 154, x + 226, y + 205), "Open")
    elif s == "collapsed_content":
        _card(draw, (280, 150, 1160, 600), "Quarterly report")
        for y in (255, 335, 415, 495):
            draw.line((320, y, 1110, y), fill=COLORS["line"], width=2)
        for x, value in ((330, "Period"), (380, "Status"), (430, "Amount")):
            _text(draw, (x, 205), value, 22, bold=True)
        for y, row in zip((280, 360, 440), (("Q1", "Ready", "42"), ("Q2", "Draft", "56"), ("Q3", "Review", "61"))):
            for x, value in zip((330, 380, 430), row):
                _text(draw, (x, y), value, 20)
    elif s == "clipped_button":
        _card(draw, (360, 145, 1080, 545), "Choose preferences", "Set the defaults for this workspace.")
        for i, label in enumerate(("Weekly digest", "Product tips", "Status updates")):
            y = 270 + i * 62
            draw.rectangle((415, y, 439, y + 24), outline=COLORS["primary"], width=2)
            _text(draw, (458, y - 2), label, 18)
        _button(draw, (760, 512, 1010, 575), "Continue")
        draw.rectangle((360, 545, 1080, 600), fill=COLORS["bg"])
    elif s == "truncated_error":
        _card(draw, (310, 155, 1130, 590), "Upload a CSV", "Map columns after the file is checked.")
        _rounded(draw, (360, 285, 1080, 347), fill=COLORS["soft_red"], outline="#F4B7C0", radius=10)
        _text(draw, (385, 302), "Import failed: unsupported col...", 18, fill=COLORS["danger"], bold=True)
        _button(draw, (820, 450, 1040, 510), "Try again")
    elif s in {"clipped_modal", "normal_modal"}:
        draw.rectangle((238, 0, WIDTH, HEIGHT), fill="#C8CDD6")
        x = 1040 if s == "clipped_modal" else 510
        heading = "Delete project" if s == "clipped_modal" else "Archive workspace"
        body = "This cannot be undone" if s == "clipped_modal" else "You can restore it later"
        _rounded(draw, (x, 185, x + 610, 535), fill="#FFFFFF", outline=COLORS["line"], radius=18)
        _text(draw, (x + 38, 230), heading, 28, bold=True)
        _text(draw, (x + 38, 290), body, 18, fill=COLORS["muted"])
        _button(draw, (x + 170, 425, x + 345, 485), "Cancel", fill="#E5E9F0", text_fill=COLORS["text"])
        _button(draw, (x + 365, 425, x + 560, 485), "Delete" if s == "clipped_modal" else "Archive", fill=COLORS["danger"] if s == "clipped_modal" else COLORS["primary"])
    elif s == "missing_nav_label":
        _card(draw, (310, 155, 1130, 590), "Navigation preview", "The third sidebar label is clipped.")
        for i, label in enumerate(("Home", "Projects", "R")):
            y = 285 + i * 68
            _rounded(draw, (390, y, 820, y + 48), fill=COLORS["soft_blue"], radius=8)
            _text(draw, (420, y + 11), label, 18, bold=True)
        draw.rectangle((448, 421, 820, 473), fill=COLORS["card"])
    elif s in {"contradictory_toggle", "normal_settings"}:
        _card(draw, (310, 155, 1130, 590), "Delivery channels", "Choose how updates reach this workspace.")
        _text(draw, (370, 300), "Email notifications", 22, bold=True)
        status = "Disabled" if s == "contradictory_toggle" else "Enabled"
        _text(draw, (370, 340), status, 17, fill=COLORS["danger"] if status == "Disabled" else COLORS["success"])
        _rounded(draw, (890, 298, 984, 348), fill=COLORS["primary"], radius=25)
        draw.ellipse((940, 303, 979, 343), fill="#FFFFFF")
        _button(draw, (820, 470, 1050, 530), "Save changes")
    elif s == "impossible_progress":
        _card(draw, (310, 160, 1130, 570), "Uploading", "large-dataset.csv")
        _rounded(draw, (380, 330, 1050, 370), fill="#E1E6EF", radius=20)
        _rounded(draw, (380, 330, 1050, 370), fill=COLORS["primary"], radius=20)
        _text(draw, (780, 250), "128%", 42, fill=COLORS["primary"], bold=True)
    elif s == "multiple_single_choice":
        _card(draw, (310, 155, 1130, 590), "Choose one plan", "You can change plans later.")
        for y, label in ((290, "Basic"), (390, "Plus")):
            _rounded(draw, (380, y, 1040, y + 76), fill=COLORS["soft_blue"], outline=COLORS["primary"], radius=12, width=2)
            draw.ellipse((410, y + 24, 438, y + 52), outline=COLORS["primary"], width=3)
            draw.ellipse((417, y + 31, 431, y + 45), fill=COLORS["primary"])
            _text(draw, (470, y + 25), label, 20, bold=True)
        _button(draw, (820, 500, 1040, 556), "Continue")
    elif s == "disabled_required_action":
        _card(draw, (310, 145, 1130, 625), "Complete your profile")
        for y, label, value in ((235, "Display name", "Workspace member"), (330, "Role", "Designer"), (425, "Workspace", "Demo Lab")):
            _text(draw, (370, y), label, 15, fill=COLORS["muted"])
            _rounded(draw, (370, y + 26, 1060, y + 76), fill="#FFFFFF", outline=COLORS["line"], radius=8)
            _text(draw, (390, y + 40), value, 17)
        _button(draw, (820, 555, 1060, 607), "Save", disabled=True)
    elif s in {"server_error", "payment_failure", "timeout_banner"}:
        if s == "server_error":
            heading, detail, action = "Could not load dashboard data", "The service returned an error.", "Retry"
        elif s == "payment_failure":
            heading, detail, action = "Payment failed", "No charge was made.", "Choose another method"
        else:
            heading, detail, action = "Live update timed out", "Last update 12 min ago", "Refresh"
        _rounded(draw, (310, 170, 1130, 300), fill=COLORS["soft_red"], outline="#F0B4BD", radius=14)
        _text(draw, (355, 205), heading, 24, fill=COLORS["danger"], bold=True)
        _text(draw, (355, 250), detail, 17, fill="#7F2835")
        _card(draw, (310, 335, 1130, 605), "Next step")
        _button(draw, (720, 455, 1060, 518), action, fill=COLORS["danger"] if s == "payment_failure" else COLORS["primary"])
    elif s == "form_validation":
        _card(draw, (330, 160, 1110, 590), "Workspace details")
        _text(draw, (390, 270), "Workspace name", 16, fill=COLORS["muted"])
        _rounded(draw, (390, 305, 1030, 365), fill="#FFFFFF", outline=COLORS["danger"], radius=8, width=2)
        _text(draw, (415, 323), "Demo Lab", 18)
        _text(draw, (390, 382), "Required field", 16, fill=COLORS["danger"], bold=True)
        _button(draw, (790, 475, 1030, 535), "Create")
    elif s == "low_contrast":
        _card(draw, (310, 155, 1130, 590), "Usage summary")
        _text(draw, (380, 300), "Current usage", 22, fill="#D5D8DE")
        _text(draw, (380, 352), "64 credits", 42, fill="#D5D8DE", bold=True)
        _rounded(draw, (760, 280, 1030, 420), fill=COLORS["soft_blue"], radius=12)
        _text(draw, (805, 325), "Monthly plan", 18, fill=COLORS["primary"], bold=True)
    elif s == "missing_focus":
        _card(draw, (310, 155, 1130, 590), "Shortcut controls", "Use Tab to move between actions.")
        _button(draw, (420, 330, 700, 395), "Save shortcut", fill="#FFFFFF", text_fill=COLORS["text"])
        _button(draw, (740, 330, 1000, 395), "Reset", fill="#FFFFFF", text_fill=COLORS["text"])
    elif s == "color_only_status":
        _card(draw, (330, 150, 1110, 610), "Service health", "Current component availability")
        for y, label, color in ((285, "API", COLORS["success"]), (375, "Storage", COLORS["danger"]), (465, "Webhooks", COLORS["success"])):
            _text(draw, (410, y), label, 22, bold=True)
            draw.ellipse((930, y + 3, 954, y + 27), fill=color)
            draw.line((410, y + 55, 970, y + 55), fill=COLORS["line"], width=1)
    elif s == "small_touch_target":
        _card(draw, (330, 160, 1110, 590), "Recent items", "Open or share a saved item.")
        for i, label in enumerate(("Research notes", "Prototype board", "Review checklist")):
            y = 275 + i * 90
            _text(draw, (400, y), label, 20, bold=True)
            for x, symbol in ((955, ">"), (1000, "+")):
                draw.rectangle((x, y, x + 18, y + 18), outline=COLORS["muted"], width=1)
                _text(draw, (x + 4, y - 2), symbol, 13, fill=COLORS["muted"], bold=True)
    else:
        raise ValueError(f"Unhandled scenario: {s}")

    return image


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8")


def generate() -> None:
    for directory in (FIXTURES, LABELS, CONTEXT, EVALS):
        if directory.exists():
            shutil.rmtree(directory)
        directory.mkdir(parents=True)

    _write_json(LABELS / "taxonomy.json", TAXONOMY)
    labels: list[dict[str, Any]] = []
    contexts: list[dict[str, Any]] = []
    tasks: list[dict[str, Any]] = []

    for spec in SPECS:
        image_path = FIXTURES / f"{spec.fixture_id}.png"
        _render(spec).save(image_path, format="PNG", optimize=False)
        digest = _sha256(image_path)
        label = {
            "fixture_id": spec.fixture_id,
            "image": f"fixtures/{image_path.name}",
            "sha256": digest,
            "width": WIDTH,
            "height": HEIGHT,
            "format": "PNG",
            "mime_type": "image/png",
            "expected_error_types": list(spec.error_types),
            "severity": spec.severity,
            "evidence": list(spec.evidence),
            "acceptable_uncertainty": spec.uncertainty,
            "visible_text": list(spec.visible_text),
            "synthetic": True,
            "contains_personal_data": False,
        }
        context = {
            "fixture_id": spec.fixture_id,
            "user_description": spec.user_description,
            "dom_summary": spec.dom_summary,
            "accessibility_snapshot": spec.accessibility_snapshot,
        }
        labels.append(label)
        contexts.append(context)
        _write_json(LABELS / f"{spec.fixture_id}.json", label)
        _write_json(CONTEXT / f"{spec.fixture_id}.json", context)

        for condition in ("image-only", "image-with-context"):
            task_id = f"{spec.fixture_id}-{condition}"
            tasks.append(
                {
                    "task_id": task_id,
                    "task_type": "vision",
                    "input": {
                        "condition": condition,
                        "image_path": f"shared/fixtures/{image_path.name}",
                        "context_path": f"shared/context/{spec.fixture_id}.json" if condition == "image-with-context" else None,
                    },
                    "attachments": [
                        {
                            "type": "image",
                            "uri": f"shared/fixtures/{image_path.name}",
                            "metadata": {"mime_type": "image/png", "sha256": digest},
                        }
                    ],
                    "constraints": {
                        "allowed_tools": ["image_preprocessor", "privacy_scanner", "deepseek_vision"],
                        "forbidden_actions": ["send_unscanned_image", "expose_personal_data", "invent_pixel_coordinates"],
                        "max_steps": 5,
                        "max_tool_calls": 3,
                    },
                    "expected_output": {
                        "fixture_id": spec.fixture_id,
                        "error_types": list(spec.error_types),
                        "severity": spec.severity,
                        "evidence": list(spec.evidence),
                        "acceptable_uncertainty": spec.uncertainty,
                    },
                    "metadata": {"condition": condition, "taxonomy_version": TAXONOMY["version"], "synthetic": True},
                }
            )

    _write_jsonl(LABELS / "labels.jsonl", labels)
    _write_jsonl(CONTEXT / "contexts.jsonl", contexts)
    _write_jsonl(EVALS / "tasks.jsonl", tasks)
    _write_json(
        ROOT / "manifest.json",
        {
            "schema_version": "1.0.0",
            "generator": "shared/generate_fixtures.py",
            "fixture_count": len(labels),
            "task_count": len(tasks),
            "dimensions": [WIDTH, HEIGHT],
            "format": "PNG",
            "fixtures": [{"fixture_id": row["fixture_id"], "sha256": row["sha256"]} for row in labels],
        },
    )


if __name__ == "__main__":
    generate()
