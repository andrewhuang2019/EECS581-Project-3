#include "lgfx/v1/LGFX_Sprite.hpp"
#define LGFX_USE_V1
#include <LovyanGFX.hpp>

class LGFX : public lgfx::LGFX_Device {
    lgfx::Panel_ST7789 _panel;
    lgfx::Bus_SPI      _bus;
    lgfx::Light_PWM    _light;

public:
LGFX() {
    {
        auto cfg = _bus.config();
        cfg.spi_host   = SPI2_HOST;
        cfg.spi_mode   = 0;
        cfg.freq_write = 40000000;
        cfg.pin_sclk   = 7;   // D8
        cfg.pin_mosi   = 9;   // D10
        cfg.pin_miso   = -1;
        cfg.pin_dc     = 2;   // D1
        _bus.config(cfg);
        _panel.setBus(&_bus);
    }
    {
        auto cfg = _panel.config();
        cfg.pin_cs       = 3;   // D2
        cfg.pin_rst      = 1;   // D0
        cfg.panel_width  = 240;
        cfg.panel_height = 280;
        cfg.invert       = true;
        cfg.offset_y = 20; // get rid of pixel rows of noise at the bottom
        _panel.config(cfg);
    }
    {
        auto cfg = _light.config();
        cfg.pin_bl      = 4;    // D3
        cfg.invert      = false;
        cfg.freq        = 44100;
        cfg.pwm_channel = 7;
        _light.config(cfg);
        _panel.setLight(&_light);
    }
        setPanel(&_panel);
    }
};

LGFX tft;
LGFX_Sprite test_sprite(&tft);

void setup() {
  tft.init();
  tft.setBrightness(255);
  tft.fillScreen(TFT_BLACK);

  test_sprite.createSprite(240, 280);
  test_sprite.pushImage(0, 0, 240, 280, test);
}

 void loop() {
  tft.fillScreen(TFT_BLACK);
  delay(1000);
  test_sprite.pushSprite(0, 0);
  delay(1000);
 }
