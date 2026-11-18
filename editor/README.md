# The WYSIWYG editor of Wissen!

Wissen! itself has no build step. Only the WYSIWYG editor is bundled once, from the
[Milkdown](https://milkdown.dev) core (ProseMirror + remark, MIT licence) – without Milkdown's
ready-made "Crepe" interface; the toolbar is Wissen!'s own.

The bundle lives in `src/wissen/static/vendor/milkdown/wissen-editor.js` and is committed,
so running or building the app needs no Node. It is loaded only when somebody switches
an open page to the formatted view.

## Rebuild

    cd editor
    npm install
    npm run build

Versions are pinned in `package.json` (`@milkdown/kit` 7.23.0, `esbuild` 0.28.2).

## What is in here

- `src/blocks.js` – block-wise write-back. A block the editor did not touch goes back to
  the file exactly as it stood there; only changed blocks are written anew. Before saving,
  the result is read back and compared with the document on screen.
- `src/editor.js` – the editor: commonmark + GFM, history, clipboard, the commands behind
  the toolbar, task-list boxes, pictures from the page's own folder.

## Check after changes

Every page must come back byte-identical when it is opened and saved unchanged. The probe
that checks this over a whole archive is described in the project notes (editor probe).
