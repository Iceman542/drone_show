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
                        String s = System.Text.Encoding.UTF8.GetString(pkt);
                        //Console.WriteLine(a);
                        drone.drone_output(s);
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

public class Drone : MonoBehaviour
{
    private Rigidbody drone_rigidbody;
    private bool bKeyPressed = false;
    private bool b_UP_Pressed = false;
    private bool b_DOWN_Pressed = false;
    private Vector3 m_pos;
    private Thread m_thread;

    // Start is called before the first frame update
    void Start()
    {
        Debug.Log("Start");

        // CREATE COMMUNICATIONS THREAD
        m_thread = new Thread(CommThread.thread_callback);
        m_thread.Start(this);


        drone_rigidbody = GetComponent<Rigidbody>();
        m_pos = drone_rigidbody.position;
    }

    public void drone_output(string s)
    {
        Debug.Log(s);
    }

    // Update is called once per frame
    void Update()
    {
        /* ALTIMETER */
        if (Input.GetKeyDown(KeyCode.W))
            m_pos.y += 1;
        if (Input.GetKeyDown(KeyCode.X))
        {
            if (m_pos.y > 0)
                m_pos.y -= 1;
        }
        if (Input.GetKeyDown(KeyCode.RightArrow))
            m_pos.x += 1;

        if (Input.GetKeyDown(KeyCode.LeftArrow))
            m_pos.x -= 1;

        if (Input.GetKeyDown(KeyCode.UpArrow))
            m_pos.z += 1;

        if (Input.GetKeyDown(KeyCode.DownArrow))
            m_pos.z -= 1;
    }

    private void FixedUpdate()
    {
        Vector3 pos = drone_rigidbody.transform.position;

        if ((m_pos.x != pos.x) || (m_pos.y != pos.y) || (m_pos.z != pos.z))
        {
            drone_rigidbody.MovePosition(m_pos);
        }

        /* Debug.Log("pos " + pos.x + " " + pos.y + " " + pos.z); */
    }

    private void OnCollisionEnter(Collision collision)
    {
        Debug.Log(collision.gameObject.name);

        /*
        drone_rigidbody.isKinematic = true;
        if (collision.gameObject.name == "Floor")
        {
            drone_rigidbody.velocity = Vector3.zero;
        }
        */
    }

    private void OnCollisionExit(Collision collision)
    {

    }
}
