/**
 * Content tests for brewspec.coffee site.
 *
 * These tests verify that result field documentation in the site source
 * matches the BrewSpec schema. They read source files directly — no
 * browser or build required.
 *
 * AC: result.dose_g and result.duration_s must appear in:
 *   1. WhatItCovers.astro — Result card field list
 *   2. schema.astro — Result section table rows
 */

import { readFileSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';
import { describe, it, expect } from 'vitest';

const __dirname = dirname(fileURLToPath(import.meta.url));

function readSource(relativePath: string): string {
  return readFileSync(join(__dirname, relativePath), 'utf-8');
}

describe('WhatItCovers.astro — Result card', () => {
  const source = readSource('components/WhatItCovers.astro');

  it('documents result.dose_g', () => {
    expect(source).toMatch(/dose.*\(g\).*actual/i);
  });

  it('documents result.duration_s', () => {
    expect(source).toMatch(/duration.*actual/i);
  });
});

describe('schema.astro — Result section table', () => {
  const source = readSource('pages/schema.astro');

  // Confirm the result section exists to anchor the assertions
  it('has a result section', () => {
    expect(source).toContain('id="result"');
  });

  it('has a table row for result.dose_g', () => {
    // The result section table must include a <code>dose_g</code> row
    // after the result section anchor — look for the code element in context
    const resultSection = source.slice(source.indexOf('id="result"'));
    expect(resultSection).toContain('<code>dose_g</code>');
  });

  it('has a table row for result.duration_s', () => {
    const resultSection = source.slice(source.indexOf('id="result"'));
    expect(resultSection).toContain('<code>duration_s</code>');
  });

  it('documents result.dose_g description', () => {
    const resultSection = source.slice(source.indexOf('id="result"'));
    // Should describe what the field records
    expect(resultSection).toMatch(/dose_g[\s\S]*?number[\s\S]*?&gt; 0/);
  });

  it('documents result.duration_s description', () => {
    const resultSection = source.slice(source.indexOf('id="result"'));
    expect(resultSection).toMatch(/duration_s[\s\S]*?number[\s\S]*?&gt; 0/);
  });
});

/**
 * CAL-2301: the field reference and the hero describe BrewSpec v1.2.
 */

function section(source: string, id: string, nextId: string): string {
  const start = source.indexOf(`id="${id}"`);
  const end = source.indexOf(`id="${nextId}"`, start);
  expect(start).toBeGreaterThan(-1);
  expect(end).toBeGreaterThan(start);
  return source.slice(start, end);
}

function row(sectionSource: string, field: string): string {
  const start = sectionSource.indexOf(`<code>${field}</code>`);
  expect(start).toBeGreaterThan(-1);
  return sectionSource.slice(start, sectionSource.indexOf('</tr>', start));
}

describe('schema.astro — v1.2 field reference', () => {
  const source = readSource('pages/schema.astro');

  it('labels itself v1.2 and links the v1.2 schema', () => {
    expect(source).toContain('v1.2 Field Reference');
    expect(source).toContain('https://brewspec.coffee/schema/v1.2.json');
    expect(source).not.toContain('v1.1');
  });

  it('documents the version const as "1.2"', () => {
    expect(row(section(source, 'top-level', 'brew'), 'brewspec_version')).toContain('"1.2"');
  });

  it('documents brew.brewed_at with a required offset', () => {
    expect(row(section(source, 'brew', 'coffee'), 'brewed_at')).toMatch(/offset/i);
  });

  it('documents brew.servings with a minimum of 1', () => {
    expect(row(section(source, 'brew', 'coffee'), 'servings')).toMatch(/minimum: 1/);
  });

  it('documents coffee.caffeine_level and its four values', () => {
    const r = row(section(source, 'coffee', 'origin'), 'caffeine_level');
    for (const value of ['regular', 'decaf', 'half_caf', 'extra']) {
      expect(r).toContain(`<code>${value}</code>`);
    }
  });

  it('lists no maxLength for coffee.cupping_notes or equipment.notes', () => {
    expect(row(section(source, 'coffee', 'origin'), 'cupping_notes')).not.toContain('maxLength');
    expect(row(section(source, 'equipment', 'result'), 'notes')).not.toContain('maxLength');
  });
});

describe('Hero.astro — v1.2', () => {
  const source = readSource('components/Hero.astro');

  it('shows a v1.2 document and the v1.2 label', () => {
    expect(source).toContain('brewspec_version: "1.2"');
    expect(source).toContain('v1.2');
    expect(source).not.toContain('v1.1');
  });
});
