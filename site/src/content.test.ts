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
    expect(resultSection).toMatch(/dose_g[\s\S]*?number[\s\S]*?> 0/);
  });

  it('documents result.duration_s description', () => {
    const resultSection = source.slice(source.indexOf('id="result"'));
    expect(resultSection).toMatch(/duration_s[\s\S]*?number[\s\S]*?> 0/);
  });
});
