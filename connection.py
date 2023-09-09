import asyncio
from viam.components.motor import Motor
from viam.robot.client import RobotClient
from viam.rpc.dial import Credentials, DialOptions


async def connect():
    creds = Credentials(
        type='robot-location-secret',
        payload='3rn6lwpqwh5xzra3sy33x8ul94b5s20zf66ghe6v9bny577z')
    opts = RobotClient.Options(
        refresh_interval=0,
        dial_options=DialOptions(credentials=creds)
    )
    return await RobotClient.at_address('robot6-main.wkhwbmlw2g.viam.cloud', opts)

async def main():
    robot = await connect()

    print('Resources:')
    print(robot.resource_names)
    left = Motor.from_robot(robot=robot, name='left')
    right = Motor.from_robot(robot=robot, name='right')
    await asyncio.gather(
        left.go_for(rpm=60, revolutions=1),
        right.go_for(rpm=60, revolutions=1)
    )

    await robot.close()

if __name__ == '__main__':
    asyncio.run(main())
