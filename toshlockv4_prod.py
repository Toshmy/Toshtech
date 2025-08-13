// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";

contract ToshLock is Ownable, ReentrancyGuard {
    using SafeERC20 for IERC20;

    address public burnAddress = 0xa9fD599cd8857e90059c83e4885Dc09986039085;

    struct Lock {
        address owner;
        uint256 amount;
        uint256 unlockTime;
        string  name;
        bool    active;
    }

    mapping(address => uint256) public tokenLockId;

    mapping(address => mapping(uint256 => Lock)) public locks;

    mapping(address => uint256[]) public tokenLockIds;
    mapping(address => mapping(address => uint256[])) public userLockIds;


    uint256 public feePercentage = 1;

    event LiquidityLocked(
        address indexed token,
        address indexed user,
        uint256 indexed lockId,
        uint256 amount,
        uint256 unlockTime,
        string  name
    );

    event LiquidityUnlocked(
        address indexed token,
        address indexed user,
        uint256 indexed lockId,
        uint256 amount
    );

    event FeeUpdated(uint256 newFee);

    constructor(address initialOwner) Ownable(initialOwner) {}

    function updateFeePercentage(uint256 newFee) external onlyOwner {
        require(newFee <= 5, "fee > 5%");
        feePercentage = newFee;
        emit FeeUpdated(newFee);
    }

    function lockLiquidityWithName(
        address token,
        uint256 amount,
        uint256 unlockTime,
        string memory name
    ) public nonReentrant {
        require(amount > 0, "amount=0");
        require(unlockTime > block.timestamp, "unlock in past");

        IERC20 erc = IERC20(token);

        erc.safeTransferFrom(msg.sender, address(this), amount);

        uint256 fee = (amount * feePercentage) / 100;
        if (fee > 0) {
            uint256 halfFee = fee / 2;
            erc.safeTransfer(owner(), halfFee); // Send 50% to contract creator
            erc.safeTransfer(burnAddress, halfFee); // Send 50% to burn address
        }
        uint256 amountAfter = amount - fee;

        uint256 newId = ++tokenLockId[token];

        locks[token][newId] = Lock({
            owner: msg.sender,
            amount: amountAfter,
            unlockTime: unlockTime,
            name: name,
            active: true
        });

        tokenLockIds[token].push(newId);
        userLockIds[msg.sender][token].push(newId);

        emit LiquidityLocked(token, msg.sender, newId, amountAfter, unlockTime, name);
    }

    function lockLiquidity(
        address token,
        uint256 amount,
        uint256 unlockTime
    ) external nonReentrant {
        lockLiquidityWithName(token, amount, unlockTime, "");
    }

    function unlockLiquidity(address token, uint256 lockId) external nonReentrant {
        Lock storage L = locks[token][lockId];
        require(L.active, "not active");
        require(L.owner == msg.sender, "not owner");
        require(block.timestamp >= L.unlockTime, "still locked");

        uint256 amt = L.amount;
        require(amt > 0, "nothing to unlock");

        L.amount = 0;
        L.active = false;

        IERC20(token).safeTransfer(msg.sender, amt);
        emit LiquidityUnlocked(token, msg.sender, lockId, amt);
    }

    function getLock(address token, uint256 lockId)
        external
        view
        returns (
            address owner,
            uint256 amount,
            uint256 unlockTime,
            string memory name,
            bool active
        )
    {
        Lock memory L = locks[token][lockId];
        return (L.owner, L.amount, L.unlockTime, L.name, L.active);
    }

    function getTokenLockCount(address token) external view returns (uint256) {
        return tokenLockIds[token].length;
    }

    function getUserLockCount(address user, address token) external view returns (uint256) {
        return userLockIds[user][token].length;
    }
    function getTokenLockIds(
        address token,
        uint256 offset,
        uint256 limit
    ) external view returns (uint256[] memory ids) {
        uint256 n = tokenLockIds[token].length;
        if (offset >= n) return new uint256[](0); // Return an empty array
        uint256 end = offset + limit;
        if (end > n) end = n;
        uint256 len = end - offset;
        ids = new uint256[](len);
        for (uint256 i = 0; i < len; i++) {
            ids[i] = tokenLockIds[token][offset + i];
        }
    }

    function getUserLockIds(
        address user,
        address token,
        uint256 offset,
        uint256 limit
    ) external view returns (uint256[] memory ids) {
        uint256 n = userLockIds[user][token].length;
        if (offset >= n) return new uint256[](0); // Return an empty array
        uint256 end = offset + limit;
        if (end > n) end = n;
        uint256 len = end - offset;
        ids = new uint256[](len);
        for (uint256 i = 0; i < len; i++) {
            ids[i] = userLockIds[user][token][offset + i];
        }
    }

    function getActiveLocksByToken(
        address token,
        uint256 offset,
        uint256 limit
    )
        external
        view
        returns (
            uint256[] memory lockIds,
            address[] memory owners,
            uint256[] memory amounts,
            uint256[] memory unlockTimes,
            string[] memory names
        )
    {
        uint256 n = tokenLockIds[token].length;
        if (offset >= n) {
            return (
                new uint256[](0),
                new address[](0),
                new uint256[](0),
                new uint256[](0),
                new string[](0)
            );
        }
        uint256 end = offset + limit;
        if (end > n) end = n;

        // Count actives first
        uint256 count = countActiveLocks(token, offset, end);

        lockIds = new uint256[](count);
        owners = new address[](count);
        amounts = new uint256[](count);
        unlockTimes = new uint256[](count);
        names = new string[](count);

        fillActiveLocksData(token, offset, end, lockIds, owners, amounts, unlockTimes, names);
    }

    function countActiveLocks(address token, uint256 offset, uint256 end) internal view returns (uint256 count) {
        for (uint256 i = offset; i < end; i++) {
            uint256 id = tokenLockIds[token][i];
            Lock memory L = locks[token][id];
            if (L.active && L.amount > 0 && L.unlockTime > block.timestamp) count++;
        }
    }

    function fillActiveLocksData(
        address token,
        uint256 offset,
        uint256 end,
        uint256[] memory lockIds,
        address[] memory owners,
        uint256[] memory amounts,
        uint256[] memory unlockTimes,
        string[] memory names
    ) internal view {
        uint256 k;
        for (uint256 i = offset; i < end; i++) {
            uint256 id = tokenLockIds[token][i];
            Lock memory L = locks[token][id];
            if (L.active && L.amount > 0 && L.unlockTime > block.timestamp) {
                lockIds[k] = id;
                owners[k] = L.owner;
                amounts[k] = L.amount;
                unlockTimes[k] = L.unlockTime;
                names[k] = L.name;
                k++;
            }
        }
    }
}
