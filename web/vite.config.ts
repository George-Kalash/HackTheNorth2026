import {defineConfig} from 'vitest/config';
import react from '@vitejs/plugin-react';
export default defineConfig({plugins:[react()],build:{rollupOptions:{output:{manualChunks:{charts:["lightweight-charts"],react:["react","react-dom","react-router-dom"],query:["@tanstack/react-query"]}}}},server:{port:5173,proxy:{'/api':{target:'http://127.0.0.1:8010',ws:true}}},test:{environment:'jsdom',setupFiles:['./src/test/setup.ts'],exclude:['e2e/**','node_modules/**']}});
