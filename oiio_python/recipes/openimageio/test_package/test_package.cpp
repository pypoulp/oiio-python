#include <OpenImageIO/imagecache.h>
#include <iostream>

int main()
{
    std::cout << "OpenImageIO " << OIIO_VERSION_STRING << std::endl;
    std::string formats = OIIO::get_string_attribute("format_list");
    std::cout << "Supported formats:\n" << formats  << std::endl;
    return 0;
}