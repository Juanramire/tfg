import { test, expect } from '@playwright/test';

test.describe('Página de inicio', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('muestra el título y subtítulo', async ({ page }) => {
    await expect(page.getByRole('heading', { name: 'PC Configurador' })).toBeVisible();
    await expect(page.getByText('Configura tu PC ideal')).toBeVisible();
  });

  test('muestra las cinco tarjetas de características', async ({ page }) => {
    await expect(page.getByText('Configuración por IA')).toBeVisible();
    await expect(page.getByText('Configurador inteligente')).toBeVisible();
    await expect(page.getByText('Optimización de presupuesto')).toBeVisible();
    await expect(page.getByText('Perfiles de uso')).toBeVisible();
    await expect(page.getByText('Notificaciones educativas')).toBeVisible();
  });

  test('el botón "Configurar con IA" navega a /consulta', async ({ page }) => {
    await page.getByRole('button', { name: 'Configurar con IA' }).click();
    await expect(page).toHaveURL('/consulta');
  });

  test('el botón "Configurar manualmente" navega a /configurar', async ({ page }) => {
    await page.getByRole('button', { name: 'Configurar manualmente' }).click();
    await expect(page).toHaveURL('/configurar');
  });

  test('al cargar lanza en segundo plano un GET a /health', async ({ page }) => {
    const health = page.waitForRequest((req) => req.url().endsWith('/health') && req.method() === 'GET');
    await page.goto('/');
    await health;
  });

  test('si /health falla no se muestra ningún error', async ({ page }) => {
    await page.route('**/health', (route) => route.abort());
    await page.goto('/');
    await expect(page.getByRole('heading', { name: 'PC Configurador' })).toBeVisible();
    await expect(page.getByRole('alert')).toHaveCount(0);
    await expect(page.getByRole('status')).toHaveCount(0);
  });
});
