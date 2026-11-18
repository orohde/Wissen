// The WYSIWYG editor of Wissen!: the Milkdown core (ProseMirror + remark) without a
// ready-made interface. The toolbar is drawn by the app; this file offers the commands.

import {
  Editor, rootCtx, defaultValueCtx, editorViewCtx, parserCtx, serializerCtx, remarkCtx, schemaCtx, commandsCtx,
} from '@milkdown/kit/core';
import {
  commonmark, toggleStrongCommand, toggleEmphasisCommand, toggleInlineCodeCommand, wrapInHeadingCommand,
  turnIntoTextCommand, wrapInBulletListCommand, wrapInOrderedListCommand, wrapInBlockquoteCommand,
  createCodeBlockCommand, insertHrCommand, insertImageCommand, toggleLinkCommand, sinkListItemCommand,
  liftListItemCommand,
} from '@milkdown/kit/preset/commonmark';
import {
  gfm, toggleStrikethroughCommand, insertTableCommand, addRowAfterCommand, addColAfterCommand,
} from '@milkdown/kit/preset/gfm';
import { history, undoCommand, redoCommand } from '@milkdown/kit/plugin/history';
import { clipboard } from '@milkdown/kit/plugin/clipboard';
import { Plugin } from '@milkdown/kit/prose/state';
import { Decoration, DecorationSet } from '@milkdown/kit/prose/view';
import { deleteRow, deleteColumn, deleteTable, isInTable } from '@milkdown/kit/prose/tables';
import { $prose } from '@milkdown/kit/utils';
import { BlockWriter } from './blocks.js';

const COMMANDS = {
  bold: [toggleStrongCommand], italic: [toggleEmphasisCommand], strike: [toggleStrikethroughCommand],
  code: [toggleInlineCodeCommand],
  h1: [wrapInHeadingCommand, 1], h2: [wrapInHeadingCommand, 2], h3: [wrapInHeadingCommand, 3],
  text: [turnIntoTextCommand],
  bullets: [wrapInBulletListCommand], numbers: [wrapInOrderedListCommand],
  indent: [sinkListItemCommand], outdent: [liftListItemCommand],
  quote: [wrapInBlockquoteCommand], codeblock: [createCodeBlockCommand], rule: [insertHrCommand],
  table: [insertTableCommand, { row: 3, col: 3 }], rowadd: [addRowAfterCommand], coladd: [addColAfterCommand],
  undo: [undoCommand], redo: [redoCommand],
};
const TABLE = { rowdel: deleteRow, coldel: deleteColumn, tabledel: deleteTable };

// "> [!NOTE]" is a callout. The marker stays ordinary text in the document (so it is written
// back unchanged); it is only shown as the coloured box the reading view draws.
const CALLOUTS = { NOTE: 'note', TIP: 'tip', IMPORTANT: 'important', WARNING: 'warning', CAUTION: 'caution', INFO: 'note' };

function calloutDecorations(doc) {
  const found = [];
  doc.descendants((node, pos) => {
    if (node.type.name !== 'blockquote') return true;
    const first = node.firstChild;
    const marker = first && first.type.name === 'paragraph' && /^\s*\[!(\w+)\]/.exec(first.textContent);
    const kind = marker && CALLOUTS[marker[1].toUpperCase()];
    // the marker must stand in the paragraph's first piece of text, or its place cannot be marked
    if (kind && first.firstChild && first.firstChild.isText && first.firstChild.text.startsWith(marker[0])) {
      found.push(Decoration.node(pos, pos + node.nodeSize, { class: `callout callout--${kind}` }));
      found.push(Decoration.inline(pos + 2, pos + 2 + marker[0].length, { class: 'callout-mark' }));
    }
    return true;
  });
  return DecorationSet.create(doc, found);
}

// the list item the cursor is in: {node, pos}, or null
function listItem(state) {
  const { $from } = state.selection;
  for (let depth = $from.depth; depth > 0; depth--) {
    const node = $from.node(depth);
    if (node.type.name === 'list_item') return { node, pos: $from.before(depth) };
  }
  return null;
}

// options: onChange() after every change of the text, onSelect({table, list}) when the cursor
// moves, imageUrl(src) to show pictures that the page names relative to its own folder
export async function create(root, markdown, options = {}) {
  const extras = $prose(() => new Plugin({
    props: {
      decorations: state => calloutDecorations(state.doc),
      nodeViews: {
        image: node => {
          const dom = document.createElement('img');
          dom.src = options.imageUrl ? options.imageUrl(node.attrs.src) : node.attrs.src;
          dom.alt = node.attrs.alt || '';
          if (node.attrs.title) dom.title = node.attrs.title;
          return { dom };
        },
      },
      // a click on the box of a task flips it
      handleClickOn(view, _pos, node, nodePos, event, direct) {
        if (!direct || node.type.name !== 'list_item' || node.attrs.checked == null) return false;
        if (event.target.tagName !== 'LI' || event.offsetX > 0) return false;
        view.dispatch(view.state.tr.setNodeMarkup(nodePos, null, { ...node.attrs, checked: !node.attrs.checked }));
        return true;
      },
    },
    view: () => ({
      update(view, before) {
        if (!view.state.doc.eq(before.doc) && options.onChange) options.onChange();
        if (options.onSelect && (!view.state.selection.eq(before.selection) || !view.state.doc.eq(before.doc))) {
          options.onSelect({ table: isInTable(view.state), list: !!listItem(view.state) });
        }
      },
    }),
  }));

  const editor = await Editor.make()
    .config(ctx => { ctx.set(rootCtx, root); ctx.set(defaultValueCtx, markdown); })
    .use(commonmark).use(gfm).use(history).use(clipboard).use(extras)
    .create();
  const ctx = editor.ctx;
  const view = ctx.get(editorViewCtx);
  const schema = ctx.get(schemaCtx);
  const writer = new BlockWriter(
    { remark: ctx.get(remarkCtx), parse: ctx.get(parserCtx), serialize: ctx.get(serializerCtx), schema },
    markdown, view.state.doc);

  return {
    view,
    traced: writer.traced,
    // {text, safe, how}: the markdown to save; safe = it reads back as what is on screen
    save: () => writer.save(view.state.doc),
    focus: () => view.focus(),
    destroy: () => editor.destroy(),
    run(name) {
      if (TABLE[name]) TABLE[name](view.state, view.dispatch);
      else if (COMMANDS[name]) ctx.get(commandsCtx).call(COMMANDS[name][0].key, COMMANDS[name][1]);
      view.focus();
    },
    // marked text becomes a link; with nothing marked the address itself is put in as one
    link(href) {
      if (!href) return;
      const { state } = view;
      if (state.selection.empty) {
        view.dispatch(state.tr.replaceSelectionWith(schema.text(href, [schema.marks.link.create({ href })]), false));
      } else ctx.get(commandsCtx).call(toggleLinkCommand.key, { href });
      view.focus();
    },
    image(src, alt = '') {
      ctx.get(commandsCtx).call(insertImageCommand.key, { src, alt });
      view.focus();
    },
    // a list item becomes a task, a task a plain item again; outside a list one is started
    task() {
      if (!listItem(view.state)) ctx.get(commandsCtx).call(wrapInBulletListCommand.key);
      const item = listItem(view.state);
      if (item) {
        view.dispatch(view.state.tr.setNodeMarkup(item.pos, null,
          { ...item.node.attrs, checked: item.node.attrs.checked == null ? false : null }));
      }
      view.focus();
    },
  };
}

window.WissenEditor = { create };
