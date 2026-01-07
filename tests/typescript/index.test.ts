import { VERSION, getVersion, greet } from '../../src/typescript/index';

describe('AicodeX TypeScript', () => {
  describe('version', () => {
    it('should have correct version constant', () => {
      expect(VERSION).toBe('0.1.0');
    });

    it('should return version from getVersion()', () => {
      expect(getVersion()).toBe('0.1.0');
    });
  });

  describe('greet', () => {
    it('should greet World by default', () => {
      expect(greet()).toBe('Hello, World from AicodeX!');
    });

    it('should greet with custom name', () => {
      expect(greet('TypeScript')).toBe('Hello, TypeScript from AicodeX!');
    });

    it('should handle empty string', () => {
      expect(greet('')).toBe('Hello,  from AicodeX!');
    });
  });
});
