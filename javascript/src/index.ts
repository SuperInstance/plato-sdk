/**
 * PLATO SDK — Tile-based knowledge store client for JavaScript/TypeScript.
 *
 * @module plato-sdk
 */

export { PlatoClient } from './client';
export { TileBuilder } from './tile';

export interface TileTags {
  tags: string[];
}

export interface TileProvenance {
  tile_id: string;
  agent_id: string;
  room: string;
  timestamp: number;
  chain_size?: number;
}

export interface Tile {
  domain?: string;
  question: string;
  answer: string;
  source?: string;
  tags: string[];
  confidence: number;
  _hash?: string;
  provenance?: TileProvenance;
  _room?: string;
}

export interface RoomInfo {
  tile_count: number;
  created: string;
}

export interface RoomDetail {
  tiles: Tile[];
  created?: string;
}
