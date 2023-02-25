package com.example.slice_simple;

import static com.example.slice_simple.SimUserGame.*;

/**
 * 对切片前后的QoE评价结果进行建模
 * k1*带宽 / (k2 * 时延 + k3 * 抖动) * e^(k4 * 丢包率)
 * 根据游戏类型配置参数吧？
 * 改在切片策略控制器中实现
 */
@Deprecated
public class QoEEvaluation {
    private double k1;
    private double k2;
    private double k3;
    private double k4;
    public static QoEEvaluation INSTANCE = null;
    private QoEEvaluation(){
        setQoEParam(1, 1, 1, 1);
    }

    /**
     * 直接设置四个参数的构造函数
     * @param p1
     * @param p2
     * @param p3
     * @param p4
     */
    private QoEEvaluation(double p1, double p2, double p3, double p4){
        setQoEParam(p1, p2, p3, p4);
    }

    /**
     * 根据切片等级构造QoE评价方式的函数
     * @param req
     */
    private QoEEvaluation(int req){
        setQoEParam(req);
    }

    public void setQoEParam(double p1, double p2, double p3, double p4){
        k1 = p1;
        k2 = p2;
        k3 = p3;
        k4 = p4;
    }

    public void setQoEParam(int req){
        switch (req){
            case REQ_DEFAULT:
                setQoEParam(1, 1, 1, 1);
                break;
            case REQ_BANDWIDTH:
                setQoEParam(4, 1, 1, 1);
                break;
            case REQ_DELAY:
                setQoEParam(1, 4, 4, 4);
                break;
            case REQ_MOBA:
                setQoEParam(2, 2, 2, 2);
                break;
        }
    }

    public QoEEvaluation getINSTANCE(){
        if(null == INSTANCE){
            INSTANCE = new QoEEvaluation();
        }
        return INSTANCE;
    }

    /**
     *
     * @param bandwidth
     * @param delay
     * @param jitter
     * @param packetLoss
     * @return 考虑根据真实情况调整参数范围
     */
    public double get_QoE_res(double bandwidth, double delay, double jitter, double packetLoss){
        double denominator = (k2 * delay + k3 * jitter) * Math.exp(packetLoss);
        return k1 * bandwidth / denominator;
    }
}
