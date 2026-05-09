/**
 * Room management helpers (re-exported for convenience).
 */

export interface RoomGroup {
  prefix: string;
  rooms: string[];
}

/** Group room IDs by prefix. */
export function groupByPrefix(
  rooms: Record<string, unknown>,
  separator: string = '_'
): RoomGroup[] {
  const groups = new Map<string, string[]>();
  for (const roomId of Object.keys(rooms).sort()) {
    const parts = roomId.split(separator, 1);
    const prefix = parts.length > 1 ? parts[0] : roomId;
    if (!groups.has(prefix)) groups.set(prefix, []);
    groups.get(prefix)!.push(roomId);
  }
  return Array.from(groups.entries()).map(([prefix, rooms]) => ({ prefix, rooms }));
}
