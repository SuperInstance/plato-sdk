/**
 * PLATO HTTP client.
 */

import type { RoomInfo, RoomDetail, Tile } from './index';

export interface PlatoClientOptions {
  timeout?: number;
}

export class PlatoClient {
  private baseUrl: string;
  private timeout: number;

  constructor(baseUrl: string, options?: PlatoClientOptions) {
    this.baseUrl = baseUrl.replace(/\/+$/, '');
    this.timeout = options?.timeout ?? 30_000;
  }

  // ------------------------------------------------------------------
  // Internal
  // ------------------------------------------------------------------

  private async request<T>(path: string, method: string = 'GET', body?: unknown): Promise<T> {
    const url = `${this.baseUrl}${path}`;
    const opts: RequestInit = {
      method,
      headers: {
        'Accept': 'application/json',
        ...(body ? { 'Content-Type': 'application/json' } : {}),
      },
      signal: AbortSignal.timeout(this.timeout),
    };
    if (body) opts.body = JSON.stringify(body);

    const resp = await fetch(url, opts);
    if (!resp.ok) {
      throw new Error(`PLATO ${resp.status}: ${resp.statusText}`);
    }
    return resp.json() as Promise<T>;
  }

  // ------------------------------------------------------------------
  // Public API
  // ------------------------------------------------------------------

  /** List all rooms with tile counts. */
  async rooms(prefix?: string): Promise<Record<string, RoomInfo>> {
    const data = await this.request<Record<string, RoomInfo>>('/rooms');
    if (prefix) {
      const filtered: Record<string, RoomInfo> = {};
      for (const [k, v] of Object.entries(data)) {
        if (k.startsWith(prefix)) filtered[k] = v;
      }
      return filtered;
    }
    return data;
  }

  /** Get room details including all tiles. */
  async room(roomId: string): Promise<RoomDetail> {
    return this.request<RoomDetail>(`/room/${encodeURIComponent(roomId)}`);
  }

  /** Submit a tile to a room. */
  async submit(roomId: string, tile: Tile | Record<string, unknown>): Promise<unknown> {
    return this.request(`/room/${encodeURIComponent(roomId)}/tile`, 'POST', tile);
  }

  /** Client-side full-text search across all rooms. */
  async search(query: string): Promise<Tile[]> {
    const q = query.toLowerCase();
    const results: Tile[] = [];
    const allRooms = await this.rooms();
    for (const roomId of Object.keys(allRooms)) {
      const detail = await this.room(roomId);
      for (const tile of detail.tiles ?? []) {
        const searchable = `${tile.question ?? ''} ${tile.answer ?? ''}`.toLowerCase();
        if (searchable.includes(q)) {
          results.push({ ...tile, _room: roomId } as Tile);
        }
      }
    }
    return results;
  }

  /** Find rooms containing tiles with a specific tag. */
  async roomsWithTag(tag: string): Promise<string[]> {
    const matched: string[] = [];
    const allRooms = await this.rooms();
    for (const roomId of Object.keys(allRooms)) {
      const detail = await this.room(roomId);
      for (const tile of detail.tiles ?? []) {
        if ((tile.tags ?? []).includes(tag)) {
          matched.push(roomId);
          break;
        }
      }
    }
    return matched;
  }

  /** Check if the PLATO server is reachable. */
  async ping(): Promise<boolean> {
    try {
      await this.rooms();
      return true;
    } catch {
      return false;
    }
  }
}
