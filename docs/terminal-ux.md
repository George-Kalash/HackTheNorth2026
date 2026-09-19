# Terminal UX

Original Parallax branding. Persistent 44px command strip, 32px tabs, 52px rail and 24px status strip; thin borders, charcoal backgrounds, amber actions, cyan Kalshi and violet Polymarket. Green/red indicate economics and book direction. Main tables use tabular monospace numbers. No fabricated KPIs or volumes.

Commands: `SRCH <query or URL>`, `COMP <match-id>`, `SCAN`, `WL`, `RULES`, `ALERTS`, `SETTINGS`. Cmd/Ctrl+K focuses the command field. Escape dismisses maximization without clearing selected contracts. Search result list supports arrows/Enter. Separator handles support pointer drag and keyboard arrows. Buttons have labels/focus states.

Presets: Research, Compare, Scan, Rules Review. Panels collapse/maximize, side panes resize, tabs close/reorder (drag or left arrow), settings resets layouts. Link A/B/C preserve independent selections/ranges/cursors. Compare preset shows a second selected link group's comparison in the right pane. Chart range controls persist; crosshair time propagates within its link group when corresponding samples exist. At narrow widths dedicated Chart/Books/Rules/Trade tabs replace the grid.

Layouts/selections/ranges persist locally. Save workspace writes a versioned database document; Settings restores it. Quotes are always queried again. Scanner virtualization bounds rendered rows; stable match IDs preserve selection as values change. Provider histories with unlike price types never share an overlay. Local comparable observations enable signed spread in percentage points.

Every import, fetch and simulation has loading/error/empty states. Browser transport status is separate from the source mode. Source pricing is labeled POLLED; connection loss never says LIVE. Retrieval time is not falsely labeled exchange timestamp. Last-good data can remain visible under explicit stale/disconnected flags.
