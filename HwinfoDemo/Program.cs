using System;
using System.Reflection;
using Hwinfo.SharedMemory;

class Program
{
    static void Main()
    {
        try
        {
            var reader = new SharedMemoryReader();
            var readings = reader.ReadLocal();

            foreach (var reading in readings)
            {
                Console.WriteLine("Reading properties:");
                foreach (PropertyInfo prop in reading.GetType().GetProperties())
                {
                    object value = prop.GetValue(reading);
                    Console.WriteLine($"  {prop.Name} = {value}");
                }
                Console.WriteLine(new string('-', 40));
            }
        }
        catch (Exception ex)
        {
            Console.WriteLine($"Error reading HWiNFO shared memory: {ex.Message}");
        }
    }
}
