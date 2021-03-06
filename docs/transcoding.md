# Transcoding

Transcoding is the process of converting from one audio format to another. This
allows for streaming of formats that wouldn't be streamable otherwise, or
reducing the quality of an audio file to allow a decent streaming for clients
with limited bandwidth, such as the ones running on a mobile connection.

Transcoding in _Supysonic_ is achieved through the use of third-party
command-line programs. _Supysonic_ isn't bundled with such programs, and you are
left to choose which one you want to use.

If you want to use transcoding but your client doesn't allow you to do so, you
can force _Supysonic_ to transcode for that client by going to your profile page
on the web interface.

## Configuration

Configuration of transcoders is done on the `[transcoding]` section of the
[configuration file](configuration.md).

Transcoding can be done by one single program which is able to convert from one
format directly to another one, or by two programs: a decoder and an encoder.
All these are defined by the following variables:

* `transcoder_EXT_EXT`
* `decoder_EXT`
* `encoder_EXT`
* `trancoder`
* `decoder`
* `encoder`

where `EXT` is the lowercase file extension of the matching audio format.
`transcoder`s variables have two extensions: the first one is the source
extension, and the second one is the extension to convert to. The same way,
`decoder`s extension is the source extension, and `encoder`s extension is the
extension to convert to.

Notice that all of them have a version without extension. Those are generic
versions. The programs defined with these variables should be able to
transcode/decode/encode any format. For that reason, we suggest you don't use
these if you want to keep control over the available transcoders.

_Supysonic_ will take the first available transcoding configuration in the
following order:

1. specific transcoder
2. specific decoder / specific encoder
3. generic decoder / generic encoder (with the possibility to use a generic
   decoder with a specific encoder, and vice-versa)
4. generic transcoder

All the variables should be set to the command-line used to run the converter
program. The command-lines can include the following fields:

* `%srcpath`: path to the original file to transcode
* `%srcfmt`: extension of the original file
* `%outfmt`: extension of the resulting file
* `%outrate`: bitrate of the resulting file

One final note: the original file should be provided as an argument of
transcoders and decoders. All transcoders, decoders and encoders should write
to standard output, and encoders should read from standard input.

## Suggested configuration

Here are some example configuration that you could use. This is provided as-is,
and some configurations haven't been tested.

```ini
[transcoding]
transcoder_mp3_mp3 = lame --quiet --mp3input -b %outrate %srcpath -
transcoder = ffmpeg -i %srcpath -ab %outratek -v 0 -f %outfmt -
decoder_mp3 = mpg123 --quiet -w - %srcpath
decoder_ogg = oggdec -o %srcpath
decoder_flac = flac -d -c -s %srcpath
encoder_mp3 = lame --quiet -b %outrate - -
encoder_ogg = oggenc2 -q -M %outrate -
```

