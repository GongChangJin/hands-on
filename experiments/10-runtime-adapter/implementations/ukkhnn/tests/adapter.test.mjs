import test from 'node:test';
import { scenarios, runScenario } from '../src/scenarios.mjs';
for (const name of Object.keys(scenarios)) test(name, () => runScenario(name));
