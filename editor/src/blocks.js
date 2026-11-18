// Block-wise write-back: what was not touched in the editor goes back to the file
// exactly as it stood there. Only blocks that changed are written anew.
//
// The source is cut into its top-level blocks (remark knows where each one starts
// and ends). The editor's document has one node per block. On saving, the nodes are
// compared with the ones from loading: a node that is still the same gets its
// original text, any other is serialised on its own.

export function sourceBlocks(remark, markdown) {
  const tree = remark.runSync(remark.parse(markdown), markdown);
  const blocks = [];
  for (const node of tree.children) {
    const pos = node.position;
    if (!pos || pos.start.offset == null || pos.end.offset == null) return null;
    blocks.push({ start: pos.start.offset, end: pos.end.offset });
  }
  for (let i = 1; i < blocks.length; i++) if (blocks[i].start < blocks[i - 1].end) return null;
  return blocks;
}

// What a node is, as text – without the ids the editor gives headings for its own use
// (they are made from the heading's text and are not part of the markdown).
const signatures = new WeakMap();
export function signature(node) {
  let text = signatures.get(node);
  if (text === undefined) {
    text = JSON.stringify(node.toJSON(), (key, value) => (key === 'id' ? undefined : value));
    signatures.set(node, text);
  }
  return text;
}

// for every new node the index of the old node it equals, or -1 (longest common subsequence)
export function align(oldNodes, newNodes) {
  const olds = oldNodes.map(node => ({ s: signature(node), eq(other) { return this.s === other.s; } }));
  const news = newNodes.map(node => ({ s: signature(node), eq(other) { return this.s === other.s; } }));
  const match = new Array(news.length).fill(-1);
  let head = 0;
  while (head < olds.length && head < news.length && olds[head].eq(news[head])) { match[head] = head; head++; }
  let oe = olds.length, ne = news.length;
  while (oe > head && ne > head && olds[oe - 1].eq(news[ne - 1])) { oe--; ne--; match[ne] = oe; }
  const n = oe - head, m = ne - head;
  if (!n || !m) return match;
  const table = Array.from({ length: n + 1 }, () => new Uint32Array(m + 1));
  for (let i = n - 1; i >= 0; i--) {
    for (let j = m - 1; j >= 0; j--) {
      table[i][j] = olds[head + i].eq(news[head + j]) ? table[i + 1][j + 1] + 1 : Math.max(table[i + 1][j], table[i][j + 1]);
    }
  }
  for (let i = 0, j = 0; i < n && j < m;) {
    if (olds[head + i].eq(news[head + j])) { match[head + j] = head + i; i++; j++; }
    else if (table[i + 1][j] >= table[i][j + 1]) i++;
    else j++;
  }
  return match;
}

export class BlockWriter {
  // parse: markdown → document, serialize: document → markdown, schema: the editor's schema
  constructor({ remark, parse, serialize, schema }, markdown, doc) {
    this.parse = parse;
    this.serialize = serialize;
    this.schema = schema;
    this.source = markdown;
    this.olds = [];
    doc.forEach(node => this.olds.push(node));
    const blocks = sourceBlocks(remark, markdown);
    // one node per block, or the text cannot be traced back: then everything is written anew
    this.blocks = blocks && blocks.length === this.olds.length ? blocks : null;
  }

  get traced() { return !!this.blocks; }

  one(node) {
    return this.serialize(this.schema.topNodeType.create(null, [node])).replace(/\n+$/, '')
      // a callout keeps its marker as it is written: "> [!NOTE]", not "> \\[!NOTE]"
      .replace(/^((?:>[ \t]*)+)\\\[!/gm, '$1[!');
  }

  whole(doc) { return this.serialize(doc).replace(/^((?:>[ \t]*)+)\\\[!/gm, '$1[!'); }

  // A changed block keeps the look of the block it replaces where that is only a matter of
  // taste: "-" as the list marker if the list had it, "---" for a divider.
  styled(node, before) {
    if (node.type.name === 'hr') return '---';
    // a single "~" stays masked: the reading view would take a pair of them for strikethrough
    let text = this.one(node).replace(/(?<![\\~])~(?!~)/g, '\\~');
    if (before && node.type.name === 'bullet_list') {
      const marker = /^[ \t]*([-+])[ \t]/.exec(before);
      if (marker) text = text.replace(/^([ \t]*)\*([ \t])/gm, `$1${marker[1]}$2`);
    }
    return text;
  }

  // the markdown for `doc`, with every untouched block as it stood in the source;
  // `keepLook` also gives changed blocks the look they had (see styled)
  write(doc, keepLook = false) {
    if (!this.blocks) return this.whole(doc);
    const { source, blocks, olds } = this;
    const news = [];
    doc.forEach(node => news.push(node));
    const match = align(olds, news);
    // which old block a changed one replaces: between the same untouched neighbours, in order
    const was = new Array(news.length).fill(null);
    if (keepLook) {
      const taken = new Set(match.filter(i => i >= 0));
      for (let j = 0; j < news.length;) {
        if (match[j] >= 0) { j++; continue; }
        let end = j;
        while (end < news.length && match[end] < 0) end++;
        const from = j > 0 ? match[j - 1] + 1 : 0;
        const to = end < news.length ? match[end] : olds.length;
        const free = [];
        for (let i = from; i < to; i++) if (!taken.has(i)) free.push(i);
        if (free.length === end - j) free.forEach((i, k) => { was[j + k] = source.slice(blocks[i].start, blocks[i].end); });
        j = end;
      }
    }
    if (!blocks.length) return news.length ? news.map(n => this.one(n)).join('\n\n') + '\n' : source;
    let out = source.slice(0, blocks[0].start);
    let prev = -2;
    news.forEach((node, j) => {
      const i = match[j];
      if (j > 0) out += i >= 0 && prev === i - 1 ? source.slice(blocks[i - 1].end, blocks[i].start) : '\n\n';
      out += i >= 0 ? source.slice(blocks[i].start, blocks[i].end) : (keepLook ? this.styled(node, was[j]) : this.one(node));
      prev = i >= 0 ? i : -2;
    });
    const tail = source.slice(blocks[blocks.length - 1].end);
    return out + (tail || '\n');
  }

  // does `markdown` read back as exactly this document?
  faithful(markdown, doc) {
    try { return signature(this.parse(markdown)) === signature(doc); } catch { return false; }
  }

  // what to save: block-wise if that reads back right, else the whole serialisation;
  // `safe` says whether the result reads back as the document on screen
  save(doc) {
    const looked = this.write(doc, true);
    if (this.faithful(looked, doc)) return { text: looked, safe: true, how: 'blocks' };
    const text = this.write(doc);
    if (this.faithful(text, doc)) return { text, safe: true, how: 'blocks' };
    const whole = this.whole(doc);
    if (this.faithful(whole, doc)) return { text: whole, safe: true, how: 'whole' };
    return { text, safe: false, how: 'blocks' };
  }
}
