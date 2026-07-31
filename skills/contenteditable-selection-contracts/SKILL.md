---
name: contenteditable-selection-contracts
description: "Use when a contenteditable or rich-text editing host loses or jumps the caret, reverses a selection, duplicates or drops edits, breaks undo/redo, inserts paste/drop content at the wrong range, corrupts an active composition through DOM replacement, or restores focus/selection after teardown. Browser editing-host transaction scope; use cjk-text-and-input for language-specific IME/Enter behavior, frontend-security-baseline for HTML sanitization policy, a11y-contract-testing for editable semantics, file-ingest-contracts for pasted/dropped files, and the relevant editor-framework skill for library document-model internals."
---

# Contenteditable selection contracts

A contenteditable failure is rarely just a cursor-coordinate bug. The browser
owns a document selection and may also own the DOM mutation and native edit
history, while application code may render a separate model over the same
nodes. This skill identifies which layer owns each edit, preserves the intended
selection across legitimate DOM replacement, and verifies one coherent editing
transaction.

## Establish the contract

Before proposing a fix, record:

1. The editing host: the nearest editable ancestor whose parent is not
   editable, not merely the descendant that received the event.
2. The ownership mode:
   - **native DOM** — allow the browser mutation, then read/reconcile it; or
   - **model-driven** — cancel a cancelable `beforeinput`, apply one model
     transaction, render once, and restore a logical selection.
3. The selection as anchor and focus node/offset plus direction. A normalized
   `Range` start/end pair alone loses backward-selection intent.
4. The event transaction: `beforeinput`/`input`, `inputType`, `data`,
   `dataTransfer`, `cancelable`, `defaultPrevented`, `isComposing`, and
   `getTargetRanges()` when available.
5. Every DOM replacement, normalization, framework commit, focus move, and
   teardown between the captured selection and the attempted restore.

Do not infer a defect from `contenteditable`, `Range`, `innerHTML`, or a
selection utility alone. Reproduce the user edit and show where the transaction
or boundary changes.

## Trace one edit end to end

1. Start with a stable host and a distinctive string containing nested inline
   markup. Place both a collapsed caret and a backward selection at known
   logical positions.
2. Capture the event order and selection before `beforeinput`, after any
   application handler, after `input`, and after the framework/render commit.
3. Compare the browser's proposed target ranges with the application
   transaction. For contenteditable edits other than history undo/redo,
   `getTargetRanges()` can expose the static ranges the browser would modify.
4. Count mutations. A model-driven transaction should not also accept a native
   mutation; a native-DOM transaction should not immediately replace equivalent
   nodes from stale model state.
5. Repeat with typing, backward/forward deletion at an inline boundary,
   paragraph insertion, undo/redo, paste, drop, and focus departure when those
   paths are in scope.

## Preserve selection without preserving stale nodes

- A document has one selection shared by its editing hosts. Filter
  document-level `selectionchange` work to the active owned host.
- Use `rangeCount` and verify both boundary nodes are connected and contained
  by the same live host before reading or restoring a captured DOM range.
- A DOM `Range` is useful during a synchronous operation while its nodes remain
  owned. It is not a durable bookmark across keyed rerenders, `innerHTML`
  replacement, route changes, or host remounts.
- Across legitimate replacement, serialize a logical bookmark in the
  application's document model: stable block/text identity plus offsets and
  selection direction. Resolve it against the committed DOM, then restore
  anchor/focus without stealing focus from a different control.
- Preserve backward selections. Use anchor/focus or an equivalent directional
  model, not only sorted start/end boundaries.
- Define fallback behavior when content was deleted: clamp to a documented
  adjacent position or intentionally clear the bookmark. Never silently restore
  into an unrelated host.

## Keep each input transaction single-owned

- `beforeinput` describes the intended edit before the browser updates the
  editing host; `input` observes the resulting change. Branch on `inputType`
  instead of reconstructing intent from key names.
- In model-driven mode, cancel only when the event is cancelable, translate the
  target range and `inputType` into one model operation, render, and restore the
  resulting logical selection.
- Some user modifications produce a non-cancelable `beforeinput`, or no
  `beforeinput` on a given browser/OS path. Treat `input` as the reconciliation
  path; do not claim complete control from a `beforeinput` handler alone.
- In native-DOM mode, let the browser edit first, then serialize the result
  without replacing the edited subtree from a stale snapshot.
- Do not use a generic keydown handler as the primary editing protocol. Keyboard
  shortcuts do not cover paste, drop, spell correction, context-menu commands,
  accessibility actions, or all composition paths.

## Respect composition boundaries

- Treat `isComposing` and the composition session as a transaction boundary.
  Do not replace the composing subtree, normalize its text nodes, or force a
  saved selection into it during `insertCompositionText`.
- Defer model normalization and selection remapping until composition has ended
  and the resulting input has been reconciled. Test the actual browser/OS/input
  method rather than assuming a universal final-event order.
- This skill owns composition only when an editing-host DOM replacement,
  selection restore, or transaction split corrupts the edit. Route CJK-specific
  Enter handling, `keyCode 229`, syllable splitting, and language/input-method
  behavior to `cjk-text-and-input`.

## Choose one undo/redo owner

- Decide whether the host uses native edit history or an application history
  stack. Record the decision for typing, formatting, paste/drop, and
  programmatic commands.
- Direct DOM/model rewrites can bypass or fragment the browser's history.
  Canceling every native edit can also leave no native entry that would trigger
  the expected undo path. Do not mix owners without an explicit bridge.
- Observe `historyUndo` and `historyRedo` as intent. Their target-range list is
  empty, so resolve the selection produced by the chosen history transaction
  rather than inventing a target range.
- Do not recommend deprecated `execCommand()` as a general architecture.
  Existing code may retain it specifically because its edits can preserve the
  native undo buffer; changing that path requires an undo/redo regression, not
  a deprecation-only rewrite.

## Normalize paste and drop at the insertion boundary

- Paste and drop are editing transactions (`insertFromPaste` and
  `insertFromDrop`) whose rich/plain payload can be exposed through
  `DataTransfer`. Choose the accepted representation once, transform it once,
  and insert it at the proposed/logical selection as one history operation.
- If overriding `paste`, cancel the default action before inserting the chosen
  payload; otherwise the browser can perform its own insertion. Apply the same
  single-owner rule to drop.
- This skill owns the insertion range, transaction count, selection afterward,
  and undo grouping. Route allowed-tag/attribute/URL policy and XSS proof to
  `frontend-security-baseline`, and route file type/size/content validation for
  pasted or dropped files to `file-ingest-contracts`.

## Focus and teardown

- Treat focus movement as user intent. Restore a bookmark only when the command
  intentionally returns focus to the same live host; toolbar pointer handling
  must not cause an unrelated control's selection to be overwritten.
- Remove document-level `selectionchange`, clipboard, drag/drop, and composition
  listeners when their owner is disposed.
- Invalidate bookmarks when their host or boundary nodes disconnect. On remount,
  create a new host ownership record instead of replaying a stale `Range`.
- Test toolbar interaction, blur to another field, host disable/removal,
  framework remount, route/dialog teardown, and late queued callbacks.

## Quick probes

- Log one compact row per event with host identity, event type, `inputType`,
  cancelability, composition state, anchor/focus paths, target ranges, and a DOM
  mutation counter.
- Temporarily stop application rerenders. If the caret remains stable, identify
  the first commit that replaces an owned boundary node.
- Compare a native-DOM path with a canceled model-driven path. If both mutate,
  the transaction has two owners.
- Type three characters, paste formatted and plain text, undo to the initial
  state, redo, then repeat after a focus round trip.

## Boundary with sibling skills

- `cjk-text-and-input` owns language- and input-method-specific composition,
  Enter, and grapheme behavior.
- `frontend-security-baseline` owns whether imported HTML is safe.
- `a11y-contract-testing` owns role, name, state, keyboard, and assistive
  technology semantics of the editor and toolbar.
- `file-ingest-contracts` owns pasted/dropped file validation and processing.
- An installed editor-framework skill owns ProseMirror, Slate, Lexical, Quill,
  Draft, or framework-specific point/node mapping after this browser-boundary
  trace establishes where the contract breaks.

## PR-worthiness gate

Require a reproducible editing sequence and observable contract failure: a
caret/selection moves to the wrong logical position, one intent produces zero
or multiple edits, undo/redo cannot round-trip the edit, paste/drop inserts at
the wrong range or twice, composition is corrupted by host mutation, or stale
focus/selection work runs after ownership ended. Capture the event/selection
trace and add the smallest browser regression that fails before the change and
passes after it.

Reject weak findings:

- `contenteditable`, `Range`, `innerHTML`, `execCommand()`, or a document
  `selectionchange` listener exists but no user-visible failure is reproduced;
- a saved range is used and all boundary nodes remain connected, contained, and
  stable for the synchronous operation;
- a `beforeinput` handler intentionally observes without canceling, and the
  native edit plus subsequent selection remain correct;
- undo behavior is asserted from source inspection without exercising typing,
  the chosen undo command, and redo;
- paste/drop payload policy is the only issue, with no selection, transaction,
  or history failure;
- the actual defect belongs to CJK IME behavior, accessibility, file ingest,
  security policy, or an editor framework's internal document mapping.

## Output shape

Start with a disposition: confirmed, candidate/needs evidence, reject, or route.
Report the live editing host and ownership mode, exact reproduction, event and
selection timeline, first stale/double-owned boundary, composition/history/
paste/focus implications, smallest fix, sibling-skill boundary, browser/OS
coverage, and the regression that checks selection plus document state and
undo/redo. For rejected findings, state why no code change is warranted.

## Sources

- W3C Selection API, document-wide selection, ranges, direction, anchor/focus,
  and `selectionchange`: <https://www.w3.org/TR/selection-api/>
- W3C Input Events Level 2, editing hosts, `beforeinput`/`input`, input types,
  composition cancelability, data transfer, target ranges, and history intent:
  <https://www.w3.org/TR/input-events-2/>
- W3C UI Events, focus, input, and composition event definitions:
  <https://www.w3.org/TR/uievents/>
- WHATWG HTML, editing hosts, `contenteditable`, focus, and drag data:
  <https://html.spec.whatwg.org/multipage/interaction.html#contenteditable>
- W3C Clipboard API and Events, clipboard data and overriding paste:
  <https://w3c.github.io/clipboard-apis/>
- MDN, `beforeinput`, including editing-host targeting and non-cancelable or
  missing paths: <https://developer.mozilla.org/en-US/docs/Web/API/Element/beforeinput_event>
- MDN, `InputEvent.getTargetRanges()`: <https://developer.mozilla.org/en-US/docs/Web/API/InputEvent/getTargetRanges>
- MDN, `InputEvent.isComposing`: <https://developer.mozilla.org/en-US/docs/Web/API/InputEvent/isComposing>
- MDN, document `selectionchange`: <https://developer.mozilla.org/en-US/docs/Web/API/Document/selectionchange_event>
- MDN, `Node.isConnected`: <https://developer.mozilla.org/en-US/docs/Web/API/Node/isConnected>
- MDN, deprecated `execCommand()` and its undo-buffer caveat:
  <https://developer.mozilla.org/en-US/docs/Web/API/Document/execCommand>
- React issue #2047, public prior art for caret jumps after a contenteditable
  rerender: <https://github.com/react/react/issues/2047>
- W3C Editing issue #509, public prior art for application-managed edits and
  native undo/redo intent: <https://github.com/w3c/editing/issues/509>
