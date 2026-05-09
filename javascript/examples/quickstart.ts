// Quick start — TypeScript example

import { PlatoClient, TileBuilder } from '../src';

const PLATO_URL = 'http://147.224.38.131:8847';

async function main() {
  const plato = new PlatoClient(PLATO_URL);

  // List rooms
  const rooms = await plato.rooms();
  console.log(`${Object.keys(rooms).length} rooms`);

  // Get room
  const room = await plato.room('fleet_health');
  console.log(`${room.tiles.length} tiles in fleet_health`);

  // Submit tile
  const tile = new TileBuilder()
    .question('SDK test tile')
    .answer('Hello from plato-sdk TypeScript!')
    .source('quickstart-example')
    .tag('test', 'sdk')
    .confidence(0.5)
    .build();

  const result = await plato.submit('test', tile);
  console.log('Submitted:', result);
}

main().catch(console.error);
