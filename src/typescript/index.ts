/**
 * AicodeX TypeScript Package
 *
 * A companion overlay code engine with hotkey support and high customizability.
 */

export const VERSION = '0.1.0';

/**
 * Returns the current version of AicodeX
 */
export function getVersion(): string {
  return VERSION;
}

/**
 * Returns a greeting message
 * @param name - The name to greet, defaults to "World"
 */
export function greet(name: string = 'World'): string {
  return `Hello, ${name} from AicodeX!`;
}

export default {
  VERSION,
  getVersion,
  greet,
};
