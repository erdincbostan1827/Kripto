import { defineConfig } from 'vite'; import react from '@vitejs/plugin-react';
export default defineConfig({plugins:[react()],server:{proxy:{'/api':{target:'http://localhost:8000'},'/health':{target:'http://localhost:8000'},'/ready':{target:'http://localhost:8000'}}},build:{sourcemap:false,target:'es2022'}});
