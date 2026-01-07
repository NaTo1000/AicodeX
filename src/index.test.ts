import { Engine, VERSION } from './index';

describe('Engine', () => {
  it('should create instance', () => {
    const engine = new Engine();
    expect(engine).toBeDefined();
  });

  it('should start and stop', () => {
    const engine = new Engine();
    expect(engine.start()).toBe(true);
    expect(engine.isRunning()).toBe(true);
    expect(engine.stop()).toBe(true);
    expect(engine.isRunning()).toBe(false);
  });

  it('should accept configuration', () => {
    const config = { debug: true };
    const engine = new Engine(config);
    expect(engine.getConfig()).toEqual(config);
  });

  it('should have version', () => {
    expect(VERSION).toBe('0.1.0');
  });
});
