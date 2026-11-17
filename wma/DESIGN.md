# Design

The application uses server-rendered Django templates under `wmaApp/templates/`, with shared structure in `wmaApp/templates/wmaApp/baseIndex.html`. Existing pages use Fomantic UI, jQuery and DataTables, with some assets loaded from CDNs. The interface includes navigation for operational management and reports, printable documents, and PWA metadata and icons.

When changing a page, follow its existing shared layout and interaction patterns, keep forms and tables usable on mobile, provide clear labels and feedback, and check keyboard access. Preserve existing user workflows and permission-dependent navigation. Verify visual changes in the browser at desktop and mobile widths. Treat these as maintenance guidelines, not a claim that every existing page meets them.
