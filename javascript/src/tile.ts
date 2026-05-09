/**
 * Tile builder for constructing PLATO tiles.
 */

import type { Tile } from './index';

export class TileBuilder {
  private _question = '';
  private _answer = '';
  private _source = '';
  private _tags: string[] = [];
  private _confidence = 0;
  private _domain = '';

  question(text: string): this {
    this._question = text;
    return this;
  }

  answer(text: string): this {
    this._answer = text;
    return this;
  }

  /** Alias for answer() — sets the tile's main content. */
  content(text: string): this {
    this._answer = text;
    return this;
  }

  source(src: string): this {
    this._source = src;
    return this;
  }

  /** Alias for source(). */
  provenance(src: string): this {
    this._source = src;
    return this;
  }

  tags(tags: string[]): this {
    this._tags.push(...tags);
    return this;
  }

  tag(...tags: string[]): this {
    this._tags.push(...tags);
    return this;
  }

  confidence(value: number): this {
    this._confidence = Math.max(0, Math.min(1, value));
    return this;
  }

  domain(d: string): this {
    this._domain = d;
    return this;
  }

  /** Build the tile object. */
  build(): Tile {
    const tile: Tile = {
      question: this._question,
      answer: this._answer,
      tags: [...this._tags],
      confidence: this._confidence,
    };
    if (this._source) tile.source = this._source;
    if (this._domain) tile.domain = this._domain;
    return tile;
  }
}
