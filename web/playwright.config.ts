import {defineConfig} from '@playwright/test';
export default defineConfig({testDir:'./e2e',timeout:90000,use:{baseURL:process.env.TERMINAL_URL??'http://127.0.0.1:8010',viewport:{width:1440,height:900}},workers:1});
