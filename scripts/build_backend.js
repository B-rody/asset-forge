/**
 * Build script for Python backend (cross-platform)
 * Run with: node scripts/build_backend.js
 */

import { spawn } from 'child_process';
import path from 'path';
import fs from 'fs';
import { fileURLToPath } from 'url';
import { dirname } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const isWindows = process.platform === 'win32';

console.log('🔨 Building AssetFurnace backend with Nuitka...\n');

const scriptPath = isWindows
  ? path.join(__dirname, 'build_backend.bat')
  : path.join(__dirname, 'build_backend.sh');

// Make shell script executable on Unix
if (!isWindows) {
  try {
    fs.chmodSync(scriptPath, '755');
  } catch (err) {
    console.error('Warning: Could not make script executable:', err.message);
  }
}

const buildProcess = spawn(scriptPath, [], {
  stdio: 'inherit',
  shell: true,
  cwd: path.join(__dirname, '..'),
});

buildProcess.on('error', (error) => {
  console.error('❌ Failed to start build process:', error);
  process.exit(1);
});

buildProcess.on('exit', (code) => {
  if (code === 0) {
    console.log('\n✅ Backend build completed successfully!');
  } else {
    console.error(`\n❌ Backend build failed with code ${code}`);
    process.exit(code);
  }
});
