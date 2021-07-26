=======================================================
Serial protocol definition for: SEL Temperature Sensor.
=======================================================

Garry Knight
2021-07-15

Serial Interface & Parameters
=============================

| Serial Interface: RS232
| BAUD: 19200
| Bits: 8
| Parity: None
| Stop Bits: 1
| Flow Control: None
| Data type: ISO8859-1

Straight Engineering Limited (SEL) Temperature instruments are multi-channel measurement instruments.
The number of channels and sensor type vary by model, but the read protocol is only affected by the number of channels.
The instruments are read only.

Data output by the SEL temperature instruments are:

    - Temperature \* n channels

Data for each channel is output as it is read and calculated by the instrument at a fixed period of approximately ~0.167 seconds.
A line terminator is added to the serial output of the final channel once all channels have been read.

Example Output Line For 4-Channel Instrument
============================================

'C01=0032.1443,C02=0033.0320,C03=-001.3020,C04=-200.0000\\r\\n'

The measurement and output line occurs over time as:

    - ... 0.167 second delay ...
    - 'C01=0032.1443,'
    - ... 0.167 second delay ...
    - 'C02=0033.0320,'
    - ... 0.167 second delay ...
    - 'C03=-001.3020,'
    - ... 0.167 second delay ...
    - 'C04=-200.0000\\r\\n'


Line Format
===========

A line consists of:

    - Channel data * n channels, delimited by comma.
    - The line is terminated immediately following the final channel data value by \\r\\n.

Channel data is in the form 'Cxx=snnn.nnnn', consisting of a prefix followed by a decimal value.

The channel data prefix is four characters:

    - 'Cxx='.
    - 'C' is the unit, Celcius.
    - 'xx' is a two character decimal integer channel number with leading zero.

The channel number is zero based, but channel '00' is reserved for the instruments internal temperature reference and not normally included in the output line.
See "Line Length" section later in this document. '=' fixed equals sign.

The temperature value is nine characters long and in the fixed form:

    - 'snnn.nnnn'.
    - 's' is the sign. Where a negative value is '-' and positive is '0' thru '9'.
    - 'n' is '0' thru '9'.
    - '.' decimal point character is fixed in the fifth position of the value.

Channel Disconnected Value
--------------------------
The instrument can report an specific value for any discoinnected temperature channel.
Disconnected temperature channel value: '999.9990'

Channel Error Value
-------------------
The instrument can report an error for any temperature channel.
Temperature channel error value: '-201.0000'

Line Length
===========
The line length is fixed, but dependent upon the number of channels.
The data output for each channel is a fixed length of 13 characters excluding delimiter.

| Delimiter length: 1
| Terminator length: 2

Line length may be calculated by number of channels as:

    - (Number of channels * 14) + 1

Some instruments may also provide the internal temperature reference value as channel #0.
In this case the line will appear to have an extra channel ('C00') in the output line.

Example Output Line For 4-Channel Instrument With Internal Reference Output
---------------------------------------------------------------------------
'C00=0024.4550,C01=0032.1443,C02=0033.0320,C03=-001.3020,C04=-200.0000\r\n'

In this case the line length may be calculated as:

    - ((Number of channels + 1) * 14) + 1

The presence of the reference value can be determined by checking the channel number of the first data value.

Recommended Integrity Checks
============================
There is no checksum or other form of integrity test supplied by the instrument in each output line.
Tests performed on the data should be performed on the basis of line length and expected format of the data.

Timeout may be used to determine if the instrument is connected/disconnected.
Timeout should occur if terminator is not received within the timeout period.
Channel data is continuously output at a rate of 0.167 seconds per channel.
A four channel instrument therefore takes 4 * 0.167 = ~0.67 seconds to complete a line.
A timeout check may be applied to a terminated line with timeout value based upoon number of channels read by the instrument.

Split output line by comma delimiter and test for correct number of channels.

Test fixed preamble for each channel number.

Test channel temperature value format and that they are convertible to float data type.
