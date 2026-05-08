const nextJest = require('next/jest');

const createJestConfig = nextJest({ dir: './' });

const config = {
  coverageProvider: 'v8',
  testEnvironment: 'jsdom',
  setupFilesAfterEnv: ['<rootDir>/jest.setup.ts'],
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/src/$1',
  },
  collectCoverageFrom: [
    'src/**/*.{ts,tsx}',
    '!src/**/*.d.ts',
    '!src/app/layout.tsx',
  ],
  testPathIgnorePatterns: ['<rootDir>/e2e/'],
};

module.exports = createJestConfig(config);
