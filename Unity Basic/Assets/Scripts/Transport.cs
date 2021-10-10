using System.Collections;
using System.Collections.Generic;
using UnityEngine;

using System;
using System.Threading;
using System.Net;
using System.Net.Sockets;
using System.Runtime.InteropServices;

static public class CommThread
{
    static byte DRONE_CMD_HEADER = 0x1f;
    static byte DRONE_CMD_FOOTER = 0xf1;
    static int DRONE_CMD_DATA_SIZE = 256;
    static int DRONE_CMD_PACKET_SIZE = 3 + DRONE_CMD_DATA_SIZE + 1;

    static int DRONE_CMD_SET_URI = 1;
    static int DRONE_CMD_START_POSITION = 2;
    static int DRONE_CMD_SET_POSITION = 3;
    static int DRONE_CMD_CLOSE = 4;

    private static void StartListening(Transport transport)
    {
        // Data buffer for incoming data.  
        byte[] bytes = new Byte[DRONE_CMD_PACKET_SIZE];

        // Establish the local endpoint for the socket.  
        // Dns.GetHostName returns the name of the
        // host running the application.  
        IPHostEntry ipHostInfo = Dns.GetHostEntry(transport.g_listening_address);
        IPAddress ipAddress = ipHostInfo.AddressList[0];
        IPEndPoint localEndPoint = new IPEndPoint(ipAddress, transport.g_listening_port);

        // Create a TCP/IP socket.  
        Socket listener = new Socket(ipAddress.AddressFamily, SocketType.Stream, ProtocolType.Tcp);

        // Bind the socket to the local endpoint and
        // listen for incoming connections.  
        try
        {
            transport.Log(String.Format("listening on {0}:{1}", transport.g_listening_address, transport.g_listening_port));

            listener.Bind(localEndPoint);
            listener.Listen(10);
            listener.SetSocketOption(SocketOptionLevel.Socket, SocketOptionName.KeepAlive, true);

            // Start listening for connections.  
            while (true)
            {
                // Program is suspended while waiting for an incoming connection.  
                Socket handler = listener.Accept();

                try
                {
                    int offset = 0;
                    int size;
                    int chunk_size;
                    byte[] temp = new byte[DRONE_CMD_PACKET_SIZE];
                    int index;
                    Vector3 pos = Vector3.zero;
                    Vector3 start_pos = Vector3.zero;

                    while (true)
                    {
                        offset = 0;

                        // READ HEADER
                        size = 3;
                        while (offset < size)
                        {
                            chunk_size = handler.Receive(temp, size - offset, 0);
                            Array.Copy(temp, 0, bytes, offset, chunk_size);
                            offset += chunk_size;
                        }

                        if (bytes[0] != DRONE_CMD_HEADER)
                            break;

                        // READ DATA & FOOTER
                        size += bytes[1] + 1;
                        while (offset < size)
                        {
                            chunk_size = handler.Receive(temp, size - offset, 0);
                            Array.Copy(temp, 0, bytes, offset, chunk_size);
                            offset += chunk_size;
                        }

                        if (bytes[size - 1] != DRONE_CMD_FOOTER)
                            break;

                        if (bytes[2] == DRONE_CMD_SET_URI)
                        {
                            index = (int)(bytes[3]);
                            byte[] pkt = new byte[DRONE_CMD_DATA_SIZE];

                            Array.Copy(bytes, 4, pkt, 0, offset - 5);
                            String s = System.Text.Encoding.UTF8.GetString(pkt);

                            transport.Log(String.Format("DRONE_CMD_SET_URI::{0}: {1}", index, s));
                        }

                        else if (bytes[2] == DRONE_CMD_START_POSITION)
                        {
                            index = (int)(bytes[3]);
                            start_pos.x = BitConverter.ToSingle(bytes, 4);
                            start_pos.y = BitConverter.ToSingle(bytes, 8);
                            start_pos.z = BitConverter.ToSingle(bytes, 12);

                            //transport.Log(String.Format("DRONE_CMD_START_POSITION::{0}: {1}, {2}, {3}", index, start_pos.x, start_pos.y, start_pos.z));

                            start_pos.x *= transport.g_xfactor;
                            start_pos.y *= transport.g_xfactor;
                            start_pos.z *= transport.g_xfactor;

                            //transport.Log(String.Format("DRONE_CMD_START_POSITION::{0}: {1}, {2}, {3}", index, start_pos.x, start_pos.y, start_pos.z));

                            transport.FlowManagerStartPosition(index, start_pos, 100f);
                        }

                        else if (bytes[2] == DRONE_CMD_SET_POSITION)
                        {
                            index = (int)(bytes[3]);
                            pos.x = BitConverter.ToSingle(bytes, 4);
                            pos.y = BitConverter.ToSingle(bytes, 8);
                            pos.z = BitConverter.ToSingle(bytes, 12);

                            //transport.Log(String.Format("DRONE_CMD_SET_POSITION::{0}: {1}, {2}, {3}", index, pos.x, pos.y, pos.z));

                            pos.x *= transport.g_xfactor;
                            pos.y *= transport.g_xfactor;
                            pos.z *= transport.g_xfactor;

                            //transport.Log(String.Format("DRONE_CMD_SET_POSITION::{0}: {1}, {2}, {3}", index, pos.x, pos.y, pos.z));

                            transport.FlowManagerPosition(index, pos, transport.g_speed);
                        }

                        else if (bytes[2] == DRONE_CMD_CLOSE)
                        {
                            transport.Log("DRONE_CMD_CLOSE");
                            break;
                        }
                    }
                }
                catch (Exception)
                {
                    transport.Log("socket exiting - ignore socket exception");
                    //transport.Log(e.ToString());
                }

                handler.Shutdown(SocketShutdown.Both);
                handler.Close();
                handler.Dispose();
            }

        }
        catch (Exception e)
        {
            transport.Log(e.ToString());
        }
    }

    public static void thread_callback(object obj)
    {
        Transport transport = (Transport)obj;
        StartListening(transport);
    }
}

public class Transport : MonoBehaviour
{
    public string g_listening_address = "192.168.1.100";
    public int g_listening_port = 9999;
    public float g_xfactor = 20f;
    public float g_speed = 0.2f;
    public int g_drone_count = 2;

    private Drone[] g_drones; 

    public void Log(string s)
    {
        Debug.Log(s);
    }

    public void FlowManagerStartPosition(int index, Vector3 pos, float speed)
    {
        try
        {
            g_drones[index].FlowManagerStartPosition(pos, speed);
        }
        catch (Exception e)
        {
            Debug.Log(e.ToString());
        }
    }

    public void FlowManagerPosition(int index, Vector3 pos, float speed)
    {
        try
        {
            g_drones[index].FlowManagerPosition(pos, speed);
        }
        catch (Exception e)
        {
            Debug.Log(e.ToString());
        }
    }

    // Start is called before the first frame update
    void Start()
    {
        Debug.Log(String.Format("Transport Initializing"));

        // FIND THE DRONE CLASS FOR EACH INSTANCE
        g_drones = new Drone[g_drone_count];
        for (int i = 0; i < g_drone_count; i++)
        {
            GameObject obj = GameObject.Find(String.Format("Vehicle{0}", i));
            if (obj == null)
                Debug.Log(String.Format("Transport - failed to find {0}", i));
            else
                g_drones[i] = (Drone)obj.GetComponent(typeof(Drone));
        }

        // CREATE COMMUNICATIONS THREAD
        Thread thread = new Thread(CommThread.thread_callback);
        thread.Start(this);
    }

    // Update is called once per frame
    void Update()
    {
        
    }
}
