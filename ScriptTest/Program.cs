using System;
using System.Threading;
using System.Net;
using System.Net.Sockets;
using System.Runtime.InteropServices;

static public class CommThread
{
    static string g_listening_address = "192.168.1.100";
    static int g_listening_port = 9999;

    private static void output(Drone drone, string s)
    {
        drone.drone_output(s);
    }

    private static void StartListening(Drone drone)
    {
        byte DRONE_CMD_HEADER = Convert.ToByte('B');
        int DRONE_CMD_SET_POSITION = 1;
        byte DRONE_CMD_FOOTER = Convert.ToByte('E');
        int DRONE_CMD_PACKET_SIZE = 35;
        int DRONE_CMD_DATA_SIZE = 32;

        // Data buffer for incoming data.  
        byte[] bytes = new Byte[DRONE_CMD_PACKET_SIZE];

        // Establish the local endpoint for the socket.  
        // Dns.GetHostName returns the name of the
        // host running the application.  
        IPHostEntry ipHostInfo = Dns.GetHostEntry(g_listening_address);
        IPAddress ipAddress = ipHostInfo.AddressList[0];
        IPEndPoint localEndPoint = new IPEndPoint(ipAddress, g_listening_port);

        // Create a TCP/IP socket.  
        Socket listener = new Socket(ipAddress.AddressFamily, SocketType.Stream, ProtocolType.Tcp);

        // Bind the socket to the local endpoint and
        // listen for incoming connections.  
        try
        {
            listener.Bind(localEndPoint);
            listener.Listen(10);

            // Start listening for connections.  
            while (true)
            {
                Console.WriteLine("Waiting for a connection...");
                // Program is suspended while waiting for an incoming connection.  
                Socket handler = listener.Accept();

                try
                {
                    int offset = 0;
                    int chunk_size;
                    byte[] temp = new byte[DRONE_CMD_PACKET_SIZE];

                    // An incoming connection needs to be processed.  
                    while (offset < DRONE_CMD_PACKET_SIZE)
                    {
                        chunk_size = handler.Receive(temp, DRONE_CMD_PACKET_SIZE - offset, 0);
                        Array.Copy(temp, 0, bytes, offset, chunk_size);
                        offset += chunk_size;
                    }

                    if ((bytes[0] == DRONE_CMD_HEADER) &&
                        (bytes[1] == DRONE_CMD_SET_POSITION) &&
                        (bytes[34] == DRONE_CMD_FOOTER))
                    {
                        byte[] pkt = new byte[DRONE_CMD_DATA_SIZE];

                        Array.Copy(bytes, 2, pkt, 0, 32);
                        String a = System.Text.Encoding.UTF8.GetString(pkt);
                        Console.WriteLine(a);
                    }
                }
                catch (Exception e)
                {
                    Console.WriteLine(e.ToString());
                }

                /*
                handler.Send(msg);
                handler.Shutdown(SocketShutdown.Both);
                handler.Close();
                */
            }

        }
        catch (Exception e)
        {
            Console.WriteLine(e.ToString());
        }

        Console.WriteLine("\nPress ENTER to continue...");
        Console.Read();

    }

    public static void thread_callback(object obj)
    {
        Drone drone = (Drone)obj;
        StartListening(drone);
    }
}

public class Drone
{
    public void drone_output(string s)
    {
        Console.WriteLine(s);
    }
}

namespace ScriptTest
{
    class Program
    {
        static void Main(string[] args)
        {
            Thread m_thread;
            Drone drone = new Drone();

            m_thread = new Thread(CommThread.thread_callback);
            m_thread.Start(drone);
        }
    }
}
