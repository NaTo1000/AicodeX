/**
 * Main index file for TypeScript module
 */

import OverlayManager, { Config } from './overlay';

export { OverlayManager, Config };

export function createOverlay(config: Config): OverlayManager {
  return new OverlayManager(config);
}
