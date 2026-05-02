import { test, expect } from '@playwright/test';

const MOCK_PROPAGATE = { forced: [], excluded: [], selectable: ['Intel', 'AMD', 'Gaming'] };

const MOCK_CONSULTA = {
  componentes: [
    {
      categoria: 'Procesador',
      producto: {
        nombre: 'Intel Core i5-12400F',
        categoria: 'Procesador',
        precio: 159.99,
        features: ['Intel', 'Intel_Gama_Media', 'LGA1700'],
        specs: {},
      },
    },
  ],
  avisos: [],
  perfil: 'Gaming',
  presupuesto: 1000,
  explicacion: 'PC gaming optimizado para jugar a 1080p',
};

test.describe('Consulta por IA', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/consulta');
  });

  test('renderiza el formulario correctamente', async ({ page }) => {
    await expect(page.getByRole('heading', { name: '¿Qué quieres hacer con tu PC?' })).toBeVisible();
    await expect(page.getByRole('textbox')).toBeVisible();
    await expect(page.getByText('Ejemplos:')).toBeVisible();
  });

  test('el botón está deshabilitado si no hay texto', async ({ page }) => {
    await expect(page.getByRole('button', { name: 'Generar configuración con IA' })).toBeDisabled();
  });

  test('clic en un ejemplo rellena el campo de texto', async ({ page }) => {
    const ejemplo = 'PC gaming de gama media para jugar a 1080p sin arruinarme';
    await page.getByText(ejemplo).click();
    await expect(page.getByRole('textbox')).toHaveValue(ejemplo);
    await expect(page.getByRole('button', { name: 'Generar configuración con IA' })).toBeEnabled();
  });

  test('consulta exitosa muestra la explicación y redirige al configurador', async ({ page }) => {
    await page.route('**/api/configuracion/consulta', (route) =>
      route.fulfill({ json: MOCK_CONSULTA })
    );
    await page.route('**/api/features/propagate', (route) =>
      route.fulfill({ json: MOCK_PROPAGATE })
    );

    await page.getByRole('textbox').fill('Quiero jugar a videojuegos');
    await page.getByRole('button', { name: 'Generar configuración con IA' }).click();

    await expect(page.getByText('PC gaming optimizado para jugar a 1080p')).toBeVisible();
    await expect(page).toHaveURL('/configurar', { timeout: 3000 });
  });

  test('error de API muestra una alerta', async ({ page }) => {
    await page.route('**/api/configuracion/consulta', (route) =>
      route.fulfill({ status: 500, json: { detail: 'Error interno del servidor' } })
    );

    await page.getByRole('textbox').fill('Quiero jugar a videojuegos');
    await page.getByRole('button', { name: 'Generar configuración con IA' }).click();

    await expect(page.getByRole('alert')).toBeVisible();
  });
});
