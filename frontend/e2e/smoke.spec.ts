import { test, expect } from '@playwright/test';

/**
 * Smoke crítico: app responde (ajusta PLAYWRIGHT_BASE_URL para staging).
 * Flujos autenticados requieren credenciales de test en entorno dedicado.
 */
test.describe('public smoke', () => {
  test('home loads and exposes Nougram title', async ({ page }) => {
    await page.goto('/');
    await expect(page).toHaveTitle(/Nougram/i);
  });

  test('login page is reachable', async ({ page }) => {
    await page.goto('/login');
    await expect(page.getByRole('heading', { name: /iniciar sesión/i })).toBeVisible({ timeout: 30_000 });
  });
});
