using System.Collections;
using System.Collections.Generic;
using UnityEngine;

using System;
using System.Threading;

public class DroneBulb
{
    public byte m_visible = 0;
    public bool m_refresh = false;
    public GameObject m_bulb_obj;
    public Color m_bulb_color;
}

public class Drone : MonoBehaviour
{
    private Rigidbody m_drone_rigidbody;
    private Vector3 m_flow_manager_start_pos;
    private Vector3 m_flow_manager_pos;
    private float m_flow_manager_speed;
    private DroneBulb[] m_bulbs;

    // Start is called before the first frame update
    void Start()
    {
        Debug.Log(String.Format("Drone Initializing - {0}", gameObject.name));

        m_drone_rigidbody = gameObject.GetComponent<Rigidbody>();
        m_flow_manager_pos = Vector3.zero;
        m_flow_manager_speed = 0f;
        m_bulbs = new DroneBulb[1];

        if (m_bulbs == null)
            Debug.Log(String.Format("m_bulbs == null"));

        string s = gameObject.name;
        int i = Int32.Parse(s.Substring(7));
        for (int j = 0; j < 1; j++)
        {
            GameObject bulb_obj = GameObject.Find(String.Format("Bulb{0}{1}", i, j));
            if (bulb_obj == null)
                Debug.Log(String.Format("Drone - failed to find Bulb{0}{1}", i, j));
            else
            {
                m_bulbs[j] = new DroneBulb();
                m_bulbs[j].m_bulb_obj = bulb_obj;
                m_bulbs[j].m_visible = 0;
                m_bulbs[j].m_refresh = true;
            }
        }
    }

    // Update is called once per frame
    void Update()
    {
        /* ALTIMETER */
        /*
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
        */
    }

    public void FlowManagerStartPosition(Vector3 pos, float speed)
    {
        m_flow_manager_start_pos.x = pos.x;
        m_flow_manager_start_pos.y = pos.y;
        m_flow_manager_start_pos.z = pos.z;

        // ISSUE1: y=z / z=y
        // ISSUE2: -40 is upstage y=-y
        // ISSUE3: 20:1 location factor

        m_flow_manager_pos.x = pos.y;
        m_flow_manager_pos.y = pos.z;
        m_flow_manager_pos.z = pos.x;
        m_flow_manager_speed = speed;


        // Debug.Log(String.Format("Start FlowManagerPosition:: {0}, {1}, {2}, {3}", m_flow_manager_pos.x, m_flow_manager_pos.y, m_flow_manager_pos.z, speed));
    }

    public void FlowManagerPosition(Vector3 pos, float speed)
    {
        Debug.Log(String.Format("BEGIN:: {0}, {1}, {2}", m_flow_manager_pos.x, m_flow_manager_pos.y, m_flow_manager_pos.z));

        pos.x = m_flow_manager_start_pos.x - pos.x;
        pos.y += m_flow_manager_start_pos.y;
        pos.z += m_flow_manager_start_pos.z;

        // ISSUE1: y=z / z=y
        // ISSUE2: -40 is upstage y=-y
        // ISSUE3: 20:1 location factor

        m_flow_manager_pos.x = pos.y;
        m_flow_manager_pos.y = pos.z;
        m_flow_manager_pos.z = pos.x;
        m_flow_manager_speed = speed;

        // Debug.Log(String.Format("FlowManagerPosition:: {0}, {1}, {2}, {3}", m_flow_manager_pos.x, m_flow_manager_pos.y, m_flow_manager_pos.z, speed));
    }

    public void FlowManagerLights(byte r, byte g, byte b)
    {
        try
        {
            m_bulbs[0].m_bulb_color.r = r;
            m_bulbs[0].m_bulb_color.g = g;
            m_bulbs[0].m_bulb_color.b = b;
            if (r == 0 && g == 0 && b == 0)
                m_bulbs[0].m_visible = 0;
            else
                m_bulbs[0].m_visible = 1;
            m_bulbs[0].m_refresh = true;

            // Debug.Log(String.Format("Lights:: {0}, {1}, {2}, {3}, {4}", bulb_index, r, g, b, visible));
        }
        catch (Exception e)
        {
            Debug.Log(e.ToString());
        }
    }

    private void FixedUpdate()
    {
        Vector3 source_pos = m_drone_rigidbody.transform.position;
        Vector3 dest_pos = m_flow_manager_pos;
        float speed = m_flow_manager_speed;
        int bulb_index;

        //Debug.Log("source_pos " + source_pos.x + " " + source_pos.y + " " + source_pos.z);
        //Debug.Log("dest_pos " + dest_pos.x + " " + dest_pos.y + " " + dest_pos.z);

        m_drone_rigidbody.transform.position = Vector3.MoveTowards(source_pos, dest_pos, speed);
        //drone_rigidbody.position = pos;
        //drone_rigidbody.MovePosition(m_pos);

        for (bulb_index = 0; bulb_index < 1; bulb_index++)
        {
            if (m_bulbs[bulb_index].m_refresh)
            {
                if (m_bulbs[bulb_index].m_visible == 1)
                {
                    m_bulbs[bulb_index].m_bulb_obj.GetComponent<Renderer>().enabled = true;
                    m_bulbs[bulb_index].m_bulb_obj.GetComponent<Renderer>().material.color = m_bulbs[bulb_index].m_bulb_color;
                }
                else
                {
                    m_bulbs[bulb_index].m_bulb_obj.GetComponent<Renderer>().enabled = false;
                    m_bulbs[bulb_index].m_bulb_obj.GetComponent<Renderer>().material.color = Color.clear;
                }

                /*if (m_bulbs[bulb_index].m_visible == 1)
                    m_bulbs[bulb_index].m_bulb_obj.GetComponent<Renderer>().material.SetOverrideTag("RenderType", "Opaque");
                else
                    m_bulbs[bulb_index].m_bulb_obj.GetComponent<Renderer>().material..SetOverrideTag("RenderType", "Transparent");
                */
                m_bulbs[bulb_index].m_refresh = false;
            }
        }            
    }

    private void OnCollisionEnter(Collision collision)
    {
        Debug.Log(collision.gameObject.name);

        /*
        drone_rigidbody.isKinematic = true;
        if (collision.gameObject.name == "Floor")
        {
            //drone_rigidbody.velocity = Vector3.zero;
        }
        */
    }

    private void OnCollisionExit(Collision collision)
    {

    }
}
