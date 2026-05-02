import { test, expect } from '@playwright/test';

const PERFILES = {
  Gaming: 'Videojuegos y entretenimiento',
  Edicion: 'Edición de vídeo y fotografía',
  Programacion: 'Desarrollo de software',
  Ofimatica: 'Trabajo de oficina',
};

const PROPAGATE = { forced: [], excluded: [], selectable: ['Intel', 'AMD', 'Gaming'] };

const CPU = {
  nombre: 'Intel Core i5-12400F',
  categoria: 'Procesador',
  precio: 159.99,
  features: ['Intel', 'Intel_Gama_Media', 'LGA1700'],
  specs: {},
};

const CONFIG_AUTO = {
  componentes: [{ categoria: 'Procesador', producto: CPU }],
  avisos: [],
  perfil: 'Gaming',
  presupuesto: 1200,
};

async function setupMocks(page) {
  await page.route('**/api/configuracion/perfiles', (route) =>
    route.fulfill({ json: PERFILES })
  );
  await page.route('**/api/features/propagate', (route) =>
    route.fulfill({ json: PROPAGATE })
  );
}

test.describe('Configurador manual', () => {
  test('muestra el stepper con el paso Perfil activo', async ({ page }) => {
    await page.route('**/api/configuracion/perfiles', (route) =>
      route.fulfill({ json: PERFILES })
    );
    await page.goto('/configurar');

    await expect(page.getByRole('heading', { name: 'Configurador de PC' })).toBeVisible();
    await expect(page.getByText('Elige tu perfil de uso')).toBeVisible();
  });

  test('seleccionar el perfil Gaming lo marca como seleccionado', async ({ page }) => {
    await setupMocks(page);
    await page.goto('/configurar');

    await page.getByText('Gaming').first().click();

    await expect(page.getByText('Seleccionado')).toBeVisible();
  });

  test('el checkbox de presupuesto muestra el slider', async ({ page }) => {
    await setupMocks(page);
    await page.goto('/configurar');

    await expect(page.getByRole('slider')).not.toBeVisible();

    await page.getByLabel('Establecer presupuesto').check();

    await expect(page.getByRole('slider')).toBeVisible();
  });

  test('generar configuración automática navega al resumen', async ({ page }) => {
    await setupMocks(page);
    await page.route('**/api/configuracion/perfil', (route) =>
      route.fulfill({ json: CONFIG_AUTO })
    );
    await page.goto('/configurar');

    await page.getByLabel('Establecer presupuesto').check();
    await page.getByText('Gaming').first().click();
    await page.getByRole('button', { name: 'Generar configuración automática' }).click();

    await expect(
      page.getByRole('heading', { name: 'Resumen de tu configuración' })
    ).toBeVisible({ timeout: 5000 });
  });

  test('el resumen muestra el componente generado y el precio total', async ({ page }) => {
    await setupMocks(page);
    await page.route('**/api/configuracion/perfil', (route) =>
      route.fulfill({ json: CONFIG_AUTO })
    );
    await page.goto('/configurar');

    await page.getByLabel('Establecer presupuesto').check();
    await page.getByText('Gaming').first().click();
    await page.getByRole('button', { name: 'Generar configuración automática' }).click();

    await expect(page.getByText('Intel Core i5-12400F')).toBeVisible({ timeout: 5000 });
    await expect(page.locator('h5').filter({ hasText: '159.99€' })).toBeVisible();
  });

  test('el botón Siguiente avanza al paso de Procesador', async ({ page }) => {
    await setupMocks(page);
    await page.route(/.*api\/productos/, (route) =>
      route.fulfill({ json: { total: 1, productos: [CPU] } })
    );
    await page.goto('/configurar');

    await page.getByRole('button', { name: 'Siguiente' }).click();

    await expect(page.getByText('Elige un procesador')).toBeVisible();
  });
});
