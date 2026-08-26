const response = context.panel.data.series[0]?.meta?.custom?.data || {};

const theme = context.grafana?.theme || {};
const colors = theme.colors || {};
const textColor = colors.text?.primary || theme.textColor || '#d1d5db';
const mutedTextColor = colors.text?.secondary || '#9ca3af';
const gridLineColor = colors.border?.weak || colors.border?.medium || 'rgba(128,128,128,0.25)';
const tooltipBackgroundColor = colors.background?.primary || 'rgba(24,24,27,0.95)';
const tooltipBorderColor = colors.border?.medium || 'rgba(128,128,128,0.35)';

const metadata = response.metadata || {};
const buckets = response.buckets || [];

const days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
const shortDays = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];

const bucketMinutes = Number(metadata.bucket_minutes ?? buckets[0]?.bucket_minutes ?? 15);
const slots = Math.floor(24 * 60 / bucketMinutes);

const hours = Array.from({ length: slots }, (_, i) => {
    const total = i * bucketMinutes;
    const h = String(Math.floor(total / 60)).padStart(2, '0');
    const m = String(total % 60).padStart(2, '0');
    return `${h}:${m}`;
});

const rawValues = buckets
    .map(bucket => Number(bucket.open_ratio ?? 0) * 100)
    .filter(value => Number.isFinite(value))
    .sort((a, b) => a - b);

const median = rawValues.length
    ? rawValues[Math.floor(rawValues.length / 2)]
    : 0;

const data = buckets
    .filter(bucket => bucket.weekday_index != null && bucket.time_index != null)
    .map(bucket => {
        const dow = Number(bucket.weekday_index);
        const tod = Number(bucket.time_index);

        const raw = Number(bucket.open_ratio ?? 0) * 100;

        let display;
        if (raw <= median) {
            display = median > 0 ? (raw / median) * 35 : 0;
        } else {
            display = 35 + ((raw - median) / Math.max(1, 100 - median)) * 65;
        }

        display = Math.max(0, Math.min(100, Math.round(display)));

        if (raw < 10) display = 0;

        const xIndex = Math.floor(tod / bucketMinutes);
        const yIndex = dow;

        return {
            value: [xIndex, yIndex, display],
            raw,
            openMinutes: Number(bucket.open_minutes ?? 0),
            openSeconds: Number(bucket.open_seconds ?? 0),
            totalBucketSeconds: Number(bucket.total_bucket_seconds ?? 0)
        };
    });

const hasData = metadata.total_events_processed > 0;

const maxValue = data.reduce((m, d) => Math.max(m, d.value[2] ?? 0), 0);

const now = new Date();
const nowDow = now.getDay();
const nowTod = now.getHours() * 60 + now.getMinutes();
const nowX = Math.floor(nowTod / bucketMinutes);
const nowY = (nowDow + 6) % 7;

const subtitleParts = [];

if (metadata.requested_start && metadata.requested_end) {
    subtitleParts.push(`${metadata.requested_start} to ${metadata.requested_end}`);
}

if (metadata.total_events_processed != null) {
    subtitleParts.push(`${metadata.total_events_processed} events`);
}

const bucketsPerHour = Math.max(1, Math.floor(60 / bucketMinutes));

const desktopXAxisInterval = Math.max(0, bucketsPerHour - 1);
const tabletXAxisInterval = Math.max(0, bucketsPerHour * 2 - 1);
const mobileXAxisInterval = Math.max(0, bucketsPerHour * 4 - 1);

const mobileZoomEnd = bucketMinutes <= 15 ? 50 : 75;

const visualMapLength = 260;
const visualMapThickness = 14;

// noinspection JSAnnotator
return {
    baseOption: {
        legend: { show: false },

        title: {
            text: 'So Make It - Open Probability',
            subtext: subtitleParts.join(' · '),
            left: 'center',
            top: 0,
            textStyle: {
                color: textColor,
                fontSize: 14,
                fontWeight: 'normal'
            },
            subtextStyle: {
                color: mutedTextColor,
                fontSize: 11
            }
        },

        tooltip: hasData ? {
            position: 'top',
            confine: true,
            triggerOn: 'mousemove|click',
            backgroundColor: tooltipBackgroundColor,
            borderColor: tooltipBorderColor,
            textStyle: {
                color: textColor,
                fontSize: 12
            },
            formatter: p => {
                const day = days[p.value[1]];
                const time = hours[p.value[0]];
                const raw = Math.round(p.data.raw);

                return [
                    `${p.marker} ${day} @ ${time}`,
                    `Open Probability: ${raw}%`
                ].join('<br/>');
            }
        } : { show: false },

        grid: {
            left: 74,
            right: 24,
            top: 58,
            bottom: hasData ? 74 : 32,
            containLabel: false
        },

        xAxis: {
            type: 'category',
            data: hours,
            splitArea: {
                show: true,
                areaStyle: {
                    color: ['rgba(128,128,128,0.03)', 'rgba(128,128,128,0.08)']
                }
            },
            axisLine: {
                lineStyle: {
                    color: gridLineColor
                }
            },
            axisTick: {
                lineStyle: {
                    color: gridLineColor
                }
            },
            axisLabel: {
                color: mutedTextColor,
                fontSize: 11,
                interval: desktopXAxisInterval
            }
        },

        yAxis: {
            type: 'category',
            data: days,
            splitArea: {
                show: true,
                areaStyle: {
                    color: ['rgba(128,128,128,0.03)', 'rgba(128,128,128,0.08)']
                }
            },
            axisLine: {
                lineStyle: {
                    color: gridLineColor
                }
            },
            axisTick: {
                lineStyle: {
                    color: gridLineColor
                }
            },
            axisLabel: {
                color: mutedTextColor,
                fontSize: 11
            },
            inverse: true
        },

        dataZoom: [],

        visualMap: hasData ? {
            show: true,
            type: 'continuous',
            min: 0,
            max: Math.max(1, maxValue),
            text: ['100%', '0%'],
            textGap: 10,
            textStyle: {
                color: mutedTextColor,
                fontSize: 12
            },
            calculable: false,
            orient: 'horizontal',
            left: 'center',
            bottom: 25,

            // For horizontal visualMap:
            // itemHeight = bar length
            // itemWidth = bar thickness
            itemHeight: visualMapLength,
            itemWidth: visualMapThickness,

            padding: [0, 0, 0, 0],
            inRange: {
                color: ['#eef6fb', '#9ecae1', '#3182bd', '#08306b'],
                opacity: [0.15, 1]
            },
            outOfRange: {
                color: 'rgba(0,0,0,0)'
            }
        } : { show: false },

        graphic: hasData ? [
            {
                type: 'text',
                left: 'center',
                bottom: 5,
                style: {
                    text: 'Open Probability',
                    fill: mutedTextColor,
                    fontSize: 12
                }
            }
        ] : [
            {
                type: 'text',
                left: 'center',
                top: 'middle',
                style: {
                    text: buckets.length === 0 ? 'No buckets returned' : 'No data',
                    fill: mutedTextColor,
                    fontSize: 14
                }
            }
        ],

        series: hasData ? [
            {
                name: 'Space Open',
                type: 'heatmap',
                data,
                animation: false,
                label: { show: false },
                emphasis: {
                    itemStyle: {
                        shadowBlur: 8,
                        shadowColor: 'rgba(0, 0, 0, 0.25)'
                    }
                },
                markLine: {
                    symbol: 'none',
                    silent: true,
                    label: { show: false },
                    lineStyle: {
                        color: '#e60000',
                        width: 2,
                        opacity: 0.8
                    },
                    data: [
                        { xAxis: nowX },
                        { yAxis: nowY }
                    ]
                }
            }
        ] : []
    },

    media: [
        {
            query: {
                maxWidth: 720
            },
            option: {
                title: {
                    text: 'Open Probability',
                    top: 2,
                    textStyle: {
                        fontSize: 13
                    },
                    subtextStyle: {
                        fontSize: 10
                    }
                },

                tooltip: {
                    position: 'inside',
                    triggerOn: 'click',
                    textStyle: {
                        fontSize: 11
                    }
                },

                grid: {
                    left: 44,
                    right: 14,
                    top: 48,
                    bottom: hasData ? 72 : 28
                },

                xAxis: {
                    axisLabel: {
                        fontSize: 10,
                        interval: tabletXAxisInterval,
                        formatter: value => {
                            const [hour, minute] = value.split(':');
                            return minute === '00' ? hour : '';
                        }
                    }
                },

                yAxis: {
                    data: shortDays,
                    axisTick: {
                        show: false
                    },
                    axisLabel: {
                        fontSize: 10
                    }
                },

                visualMap: hasData ? {
                    bottom: 18,

                    // For horizontal visualMap:
                    // itemHeight = bar length
                    // itemWidth = bar thickness
                    itemHeight: visualMapLength,
                    itemWidth: 12,

                    text: ['100%', '0%'],
                    textStyle: {
                        fontSize: 11
                    }
                } : { show: false },

                graphic: hasData ? [] : [
                    {
                        type: 'text',
                        left: 'center',
                        top: 'middle',
                        style: {
                            text: buckets.length === 0 ? 'No buckets returned' : 'No data',
                            fill: mutedTextColor,
                            fontSize: 12
                        }
                    }
                ],

                series: [
                    {
                        markLine: {
                            lineStyle: {
                                width: 1
                            }
                        },
                        emphasis: {
                            itemStyle: {
                                shadowBlur: 4
                            }
                        }
                    }
                ]
            }
        },

        {
            query: {
                maxWidth: 480
            },
            option: {
                title: {
                    text: 'Open',
                    subtext: '',
                    textStyle: {
                        fontSize: 12
                    }
                },

                grid: {
                    left: 38,
                    right: 10,
                    top: 36,
                    bottom: hasData ? 46 : 24
                },

                xAxis: {
                    splitArea: {
                        show: false
                    },
                    axisTick: {
                        show: false
                    },
                    axisLabel: {
                        fontSize: 9,
                        interval: mobileXAxisInterval,
                        rotate: 0,
                        formatter: value => {
                            const [hour, minute] = value.split(':');
                            return minute === '00' ? hour : '';
                        }
                    }
                },

                yAxis: {
                    data: shortDays,
                    splitArea: {
                        show: false
                    },
                    axisTick: {
                        show: false
                    },
                    axisLabel: {
                        fontSize: 9
                    }
                },

                dataZoom: hasData ? [
                    {
                        type: 'inside',
                        xAxisIndex: 0,
                        filterMode: 'none',
                        zoomOnMouseWheel: false,
                        moveOnMouseMove: true,
                        moveOnMouseWheel: true,
                        preventDefaultMouseMove: true,
                        start: 0,
                        end: mobileZoomEnd
                    },
                    {
                        type: 'slider',
                        xAxisIndex: 0,
                        filterMode: 'none',
                        height: 12,
                        bottom: 14,
                        left: 38,
                        right: 10,
                        brushSelect: false,
                        showDetail: false,
                        showDataShadow: false,
                        borderColor: gridLineColor,
                        fillerColor: 'rgba(128,128,128,0.18)',
                        handleStyle: {
                            color: mutedTextColor
                        },
                        moveHandleStyle: {
                            color: mutedTextColor
                        }
                    }
                ] : [],

                visualMap: {
                    show: false
                }
            }
        },

        {
            query: {
                maxHeight: 300
            },
            option: {
                title: {
                    subtext: ''
                },

                grid: {
                    top: 32,
                    bottom: hasData ? 42 : 20
                },

                visualMap: {
                    show: false
                },

                graphic: []
            }
        }
    ]
};