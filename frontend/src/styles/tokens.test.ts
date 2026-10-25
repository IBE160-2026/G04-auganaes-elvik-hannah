// Story 1.1 (AD-13): design tokens come from one source and components only use var(--...).
import { readdirSync, readFileSync } from 'node:fs';
import { dirname, join, relative, sep } from 'node:path';
import { fileURLToPath } from 'node:url';

const STYLES_DIR = dirname(fileURLToPath(import.meta.url));
const SRC_DIR = dirname(STYLES_DIR);
const DESIGN_MD = join(
  SRC_DIR,
  '../../_bmad-output/planning-artifacts/ux-designs/ux-prosjektoppgave-ibe160-2026-09-29/DESIGN.md',
);

/** Files allowed to use the pill radius (DESIGN.md Shapes: primary button, badges, status tags). */
const PILL_ALLOWED = /^(PrimaryButton|Badge|StatusTag)[^/\\]*\.css$/;

const COLOR_PROPERTIES = new Set([
  'color',
  'background',
  'background-color',
  'background-image',
  'border',
  'border-top',
  'border-right',
  'border-bottom',
  'border-left',
  'border-color',
  'outline',
  'outline-color',
  'box-shadow',
  'text-shadow',
  'text-decoration-color',
  'caret-color',
  'accent-color',
  'fill',
  'stroke',
]);

const LENGTH_PROPERTY = new RegExp(
  '^(' +
    [
      'padding(-.+)?',
      'margin(-.+)?',
      'gap',
      'row-gap',
      'column-gap',
      'border-(.+-)?radius',
      'box-shadow',
      'text-shadow',
      '(min-|max-)?(width|height|inline-size|block-size)',
      'font',
      'font-size',
      'letter-spacing',
      'flex(-basis)?',
      'outline(-width|-offset)?',
      'inset(-.+)?',
      'top',
      'right',
      'bottom',
      'left',
    ].join('|') +
    ')$',
);

// CSS named colors (CSS Color 4). "transparent" and "currentcolor" are keywords, not palette colors.
const NAMED_COLORS = new Set(
  (
    'aliceblue antiquewhite aqua aquamarine azure beige bisque black blanchedalmond blue blueviolet ' +
    'brown burlywood cadetblue chartreuse chocolate coral cornflowerblue cornsilk crimson cyan ' +
    'darkblue darkcyan darkgoldenrod darkgray darkgreen darkgrey darkkhaki darkmagenta ' +
    'darkolivegreen darkorange darkorchid darkred darksalmon darkseagreen darkslateblue ' +
    'darkslategray darkslategrey darkturquoise darkviolet deeppink deepskyblue dimgray dimgrey ' +
    'dodgerblue firebrick floralwhite forestgreen fuchsia gainsboro ghostwhite gold goldenrod gray ' +
    'green greenyellow grey honeydew hotpink indianred indigo ivory khaki lavender lavenderblush ' +
    'lawngreen lemonchiffon lightblue lightcoral lightcyan lightgoldenrodyellow lightgray ' +
    'lightgreen lightgrey lightpink lightsalmon lightseagreen lightskyblue lightslategray ' +
    'lightslategrey lightsteelblue lightyellow lime limegreen linen magenta maroon ' +
    'mediumaquamarine mediumblue mediumorchid mediumpurple mediumseagreen mediumslateblue ' +
    'mediumspringgreen mediumturquoise mediumvioletred midnightblue mintcream mistyrose moccasin ' +
    'navajowhite navy oldlace olive olivedrab orange orangered orchid palegoldenrod palegreen ' +
    'paleturquoise palevioletred papayawhip peachpuff peru pink plum powderblue purple ' +
    'rebeccapurple red rosybrown royalblue saddlebrown salmon sandybrown seagreen seashell sienna ' +
    'silver skyblue slateblue slategray slategrey snow springgreen steelblue tan teal thistle ' +
    'tomato turquoise violet wheat white whitesmoke yellow yellowgreen'
  ).split(' '),
);

export type Violation = { line: number; rule: string; text: string };

function stripComments(source: string): string {
  // Keep newlines so reported line numbers stay correct.
  return source
    .replace(/\/\*[\s\S]*?\*\//g, (comment) => comment.replace(/[^\n]/g, ' '))
    .replace(/(^|[^:'"])\/\/[^\n]*/g, (_match, prefix: string) => prefix);
}

function kebab(property: string): string {
  return property.replace(/[A-Z]/g, (char) => `-${char.toLowerCase()}`);
}

/** A literal length other than zero, e.g. 12px, -1.5rem, 2em (not part of a name like a-12px). */
const LITERAL_LENGTH = /(?<![\w.-])(-?)(\d*\.?\d+)(px|rem|em)\b/g;

/** A bare number as a whole TSX style value, e.g. `padding: 12` (React adds px). */
const BARE_NUMBER = /^-?\d*\.?\d+$/;

function hasLiteralLength(value: string, allowOnePx: boolean): boolean {
  for (const match of value.matchAll(LITERAL_LENGTH)) {
    const amount = Number(match[2]);
    if (amount === 0) continue;
    if (allowOnePx && !match[1] && amount === 1 && match[3] === 'px') continue;
    return true;
  }
  return false;
}

/** Scan one component file (CSS or TSX) for values that should be design tokens. */
export function findViolations(source: string, fileName: string): Violation[] {
  const violations: Violation[] = [];
  const lines = stripComments(source).split('\n');
  const pillAllowed = PILL_ALLOWED.test(fileName);
  const isTsx = fileName.endsWith('.tsx');

  lines.forEach((rawLine, index) => {
    const line = rawLine.trim();
    if (line.startsWith('@media')) return;
    const report = (rule: string) => violations.push({ line: index + 1, rule, text: line });

    if (/#[0-9a-fA-F]{3,8}\b/.test(line) && !/href=["']#/.test(line)) report('hex color');
    if (/\b(rgba?|hsla?)\(/.test(line)) report('rgb()/hsl() color');
    if (/--radius-full/.test(line) && !pillAllowed) report('--radius-full outside pill components');

    // Declarations: CSS `prop: value;` or a TSX style object `prop: 'value'`.
    const declaration = /([a-zA-Z-]+)\s*:\s*['"]?([^;'"{}]+)/g;
    for (const [, rawProperty, rawValue] of line.matchAll(declaration)) {
      const property = kebab(rawProperty);
      const value = rawValue.replace(/var\([^)]*\)/g, ' ').trim();

      if (/^outline(-width)?$/.test(property) && /^(none|0)\b/.test(value)) report('outline removed');
      if (COLOR_PROPERTIES.has(property)) {
        const words = value.toLowerCase().match(/[a-z]+/g) ?? [];
        if (words.some((word) => NAMED_COLORS.has(word))) report('named color');
      }
      if (LENGTH_PROPERTY.test(property) && hasLiteralLength(value, false)) report('literal length');
      // `flex` is unitless in React style objects (flex-grow), so only real lengths count here.
      if (isTsx && property !== 'flex' && LENGTH_PROPERTY.test(property)) {
        if (BARE_NUMBER.test(value) && Number(value) !== 0) report('numeric length in style');
      }
      if (/^border(-(top|right|bottom|left))?(-width)?$/.test(property)) {
        if (hasLiteralLength(value, true)) report('literal border width (only 1px allowed)');
      }
    }
  });

  return violations;
}

function componentFiles(): string[] {
  return readdirSync(SRC_DIR, { recursive: true, encoding: 'utf8' })
    .filter((file) => /\.(css|tsx)$/.test(file))
    .filter((file) => !file.startsWith(`styles${sep}`))
    .filter((file) => !/\.test\.tsx$/.test(file));
}

function frontmatterGroup(markdown: string, group: string): Record<string, string> {
  const frontmatter = markdown.split(/^---$/m)[1] ?? '';
  const block = frontmatter.match(new RegExp(`^${group}:\\n((?:  .*\\n)+)`, 'm'))?.[1] ?? '';
  const entries: Record<string, string> = {};
  for (const [, key, value] of block.matchAll(/^ {2}'?([\w-]+)'?:\s*'?([^'\n]+)'?$/gm)) {
    entries[key] = value.trim();
  }
  return entries;
}

describe('findViolations (the AD-13 checker itself)', () => {
  it.each([
    ['color: #6E62CC;', 'hex color'],
    ['background: rgb(0 0 0);', 'rgb()/hsl() color'],
    ['color: hsl(250 50% 59%);', 'rgb()/hsl() color'],
    ['background-color: white;', 'named color'],
    ["style={{ backgroundColor: 'red' }}", 'named color'],
    ['padding: 12px;', 'literal length'],
    ['margin: var(--space-2) 1rem;', 'literal length'],
    ['gap: 0.5em;', 'literal length'],
    ['border-radius: 14px;', 'literal length'],
    ['box-shadow: 0 var(--space-1) 6px var(--color-ink-primary);', 'literal length'],
    ['min-height: 44px;', 'literal length'],
    ['margin: -12px;', 'literal length'],
    ['margin-top: calc(var(--space-2) * -1) -0.5rem;', 'literal length'],
    ['font: 700 16px/1.2 var(--font-family);', 'literal length'],
    ['letter-spacing: 0.03em;', 'literal length'],
    ['flex-basis: 200px;', 'literal length'],
    ['flex: 1 1 12rem;', 'literal length'],
    ["style={{ paddingTop: '8px' }}", 'literal length'],
    ['outline: none;', 'outline removed'],
    ['outline: 0;', 'outline removed'],
    ['border: 2px solid var(--color-accent);', 'literal border width (only 1px allowed)'],
    ['border-radius: var(--radius-full);', '--radius-full outside pill components'],
  ])('flags %s', (source, rule) => {
    expect(findViolations(source, 'Card.css').map((v) => v.rule)).toContain(rule);
  });

  it.each([
    'padding: var(--space-3) var(--space-5);',
    'border: 1px solid var(--color-accent);',
    'border: none;',
    'margin: 0;',
    'background: none;',
    'color: currentcolor;',
    'background: transparent;',
    'outline: var(--focus-width) solid var(--focus-color);',
    '@media (min-width: 37.5em) {',
    '/* was #6E62CC and 12px */',
    'transform: translateY(-200%);',
    '<a href="#hovedinnhold">',
    'min-height: 100dvh;',
  ])('accepts %s', (source) => {
    expect(findViolations(source, 'Card.css')).toEqual([]);
  });

  it.each([
    ['style={{ padding: 12 }}', 'numeric length in style'],
    ['style={{ marginTop: -8 }}', 'numeric length in style'],
    ['style={{ flexBasis: 200 }}', 'numeric length in style'],
    ['style={{ letterSpacing: 1 }}', 'numeric length in style'],
  ])('flags %s in a TSX file', (source, rule) => {
    expect(findViolations(source, 'Card.tsx').map((v) => v.rule)).toContain(rule);
  });

  it.each(['style={{ padding: 0 }}', 'style={{ flex: 1 }}'])('accepts %s in a TSX file', (source) => {
    expect(findViolations(source, 'Card.tsx')).toEqual([]);
  });

  it('allows --radius-full in PrimaryButton.css and badge files', () => {
    const source = 'border-radius: var(--radius-full);';
    expect(findViolations(source, 'PrimaryButton.css')).toEqual([]);
    expect(findViolations(source, 'BadgeMust.css')).toEqual([]);
  });
});

describe('component files', () => {
  const files = componentFiles();

  it('finds the component files to check', () => {
    expect(files.length).toBeGreaterThan(0);
  });

  it.each(files)('%s uses only design tokens', (file) => {
    const source = readFileSync(join(SRC_DIR, file), 'utf8');
    const name = relative(SRC_DIR, join(SRC_DIR, file)).split(sep).pop() ?? file;
    expect(findViolations(source, name)).toEqual([]);
  });
});

describe('tokens.css matches DESIGN.md', () => {
  const tokens = readFileSync(join(STYLES_DIR, 'tokens.css'), 'utf8');
  const design = readFileSync(DESIGN_MD, 'utf8');
  const groups = {
    colors: frontmatterGroup(design, 'colors'),
    spacing: frontmatterGroup(design, 'spacing'),
    rounded: frontmatterGroup(design, 'rounded'),
  };
  const ROLES = ['display', 'title', 'body', 'meta', 'badge'];

  function tokenValue(name: string): string | undefined {
    return tokens.match(new RegExp(`--${name}:\\s*([^;]+);`))?.[1].trim();
  }

  /** The indented block under `  <name>:` in the frontmatter (typography roles, components). */
  function nestedBlock(name: string): string {
    return design.match(new RegExp(`^  ${name}:\\n((?:    .*\\n)+)`, 'm'))?.[1] ?? '';
  }

  function field(block: string, key: string): string | undefined {
    return block.match(new RegExp(`^\\s+${key}:\\s*(.+)$`, 'm'))?.[1].trim().replace(/^"(.*)"$/, '$1');
  }

  /** Compare CSS values without caring about spaces or a leading zero (".05" vs "0.05"). */
  function normalize(value: string | undefined): string | undefined {
    return value?.replace(/\s+/g, '').replace(/(^|[^\d.])0\./g, '$1.');
  }

  it.each(Object.entries(groups))('parses a non-empty %s group from DESIGN.md', (_name, group) => {
    expect(Object.keys(group).length).toBeGreaterThan(0);
  });

  it.each(ROLES)('parses a non-empty typography.%s block from DESIGN.md', (role) => {
    expect(nestedBlock(role)).not.toBe('');
  });

  it.each(Object.entries(groups.colors))('--color-%s is %s', (key, value) => {
    expect(tokenValue(`color-${key}`)?.toUpperCase()).toBe(value.toUpperCase());
  });

  it.each(Object.entries(groups.spacing))('--space-%s is %s', (key, value) => {
    expect(tokenValue(`space-${key}`)).toBe(value);
  });

  it.each(Object.entries(groups.rounded))('--radius-%s is %s', (key, value) => {
    expect(tokenValue(`radius-${key.toLowerCase()}`)).toBe(value);
  });

  it.each(ROLES)('typography %s is copied', (role) => {
    const block = nestedBlock(role);
    expect(tokenValue('font-family')).toBe(field(block, 'fontFamily'));
    expect(tokenValue(`font-size-${role}`)).toBe(field(block, 'fontSize'));
    expect(tokenValue(`font-weight-${role}`)).toBe(field(block, 'fontWeight'));
    expect(tokenValue(`line-height-${role}`)).toBe(field(block, 'lineHeight'));
  });

  it('badge letter spacing is copied', () => {
    const letterSpacing = field(nestedBlock('badge'), 'letterSpacing');
    expect(letterSpacing).toBeDefined();
    expect(tokenValue('letter-spacing-badge')).toBe(letterSpacing);
  });

  it('focus ring width and offset match components.focus-outline', () => {
    const block = nestedBlock('focus-outline');
    expect(field(block, 'width')).toBeDefined();
    expect(tokenValue('focus-width')).toBe(field(block, 'width'));
    expect(tokenValue('focus-offset')).toBe(field(block, 'offset'));
  });

  it('card shadow matches the one documented in Elevation & Depth', () => {
    const documented = design.match(/single soft, low-opacity shadow \(`([^`]+)`/)?.[1];
    expect(documented).toBeDefined();
    expect(normalize(tokenValue('shadow-card'))).toBe(normalize(documented));
  });

  it('tap target minimum is 44px at a 16px root', () => {
    expect(tokenValue('tap-min')).toBe('2.75rem');
  });

  it('manifest.json and index.html theme colors equal the tokens', () => {
    const root = dirname(SRC_DIR);
    const manifest = JSON.parse(readFileSync(join(root, 'public/manifest.json'), 'utf8'));
    const html = readFileSync(join(root, 'index.html'), 'utf8');
    const metaThemeColor = html.match(/<meta name="theme-color" content="([^"]+)"/)?.[1];

    expect(manifest.theme_color.toUpperCase()).toBe(tokenValue('color-primary')?.toUpperCase());
    expect(manifest.background_color.toUpperCase()).toBe(
      tokenValue('color-surface-base')?.toUpperCase(),
    );
    expect(metaThemeColor?.toUpperCase()).toBe(tokenValue('color-primary')?.toUpperCase());
  });
});
