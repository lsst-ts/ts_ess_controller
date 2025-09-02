#include "sps30.h"
#include "sensirion_uart.h"
#include <stdio.h>
#include <unistd.h>

int main() {
    int16_t ret;
    struct sps30_measurement m;

    ret = sensirion_uart_open("/dev/ttyUSB0");
    if (ret != 0) {
        printf("ERROR: Failed to open UART device\n");
        return 1;
    }

    ret = sps30_probe();
    if (ret) {
        printf("ERROR: SPS30 sensor not found\n");
        return 1;
    }

    ret = sps30_start_measurement();
    if (ret) {
        printf("ERROR: Could not start measurement\n");
        return 1;
    }

    sleep(2); // Wait for measurement

    ret = sps30_read_measurement(&m);
    if (ret) {
        printf("ERROR: Could not read measurement\n");
        return 1;
    }

    printf("{\"pm1.0\": %.1f, \"pm2.5\": %.1f, \"pm4.0\": %.1f, \"pm10\": %.1f}\n",
           m.mc_1p0, m.mc_2p5, m.mc_4p0, m.mc_10p0);

    sps30_stop_measurement();
    return 0;
}
